"""
ElectaVerse — Master Simulation Engine
Runs real-time election day simulation. ALL config loaded from MySQL.
"""

import time
import threading
from datetime import datetime
from simulation.election_clock import ElectionClock
from simulation.queue_dynamics import QueueDynamics
from simulation.incident_injector import IncidentInjector
from models.booth import Booth
from models.incident import Incident
from db.connection import Database


class SimulationEngine:
    """Master simulation controller — DB-driven, runs in background thread."""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.is_paused = False
        self.booths: list[Booth] = []
        self.incidents: list[Incident] = []
        self.incident_tick_map: dict[str, int] = {}
        self.turnout_history: list[dict] = []
        self.running = False
        self._thread = None

        # Load ALL config from DB
        self._sim_config = {}
        self._peak_multipliers = {}
        self.clock = None
        self.incident_injector = None
        self._load_config()

    def _load_config(self):
        """Load all simulation parameters from MySQL."""
        # Simulation config
        rows = Database.execute("SELECT config_key, config_value FROM simulation_config")
        for row in rows:
            self._sim_config[row['config_key']] = row['config_value']

        # Peak multipliers
        rows = Database.execute("SELECT hour, multiplier FROM peak_multipliers")
        for row in rows:
            self._peak_multipliers[int(row['hour'])] = float(row['multiplier'])

        # Create clock from DB config
        self.clock = ElectionClock(
            start_hour=int(self._sim_config.get('election_start_hour', 7)),
            end_hour=int(self._sim_config.get('election_end_hour', 18)),
            minutes_per_tick=int(self._sim_config.get('simulated_minutes_per_tick', 2)),
        )

        # Incident config from DB
        incident_rows = Database.execute("SELECT * FROM incident_config")
        self.incident_injector = IncidentInjector(incident_rows)

        # Load booths from DB
        self._load_booths()

    def _load_booths(self):
        """Load all booths from MySQL."""
        rows = Database.execute("""
            SELECT b.id, b.name, b.constituency_id, c.name as constituency_name,
                   b.lat, b.lng, b.registered_voters, b.base_throughput
            FROM booths b
            JOIN constituencies c ON b.constituency_id = c.id
        """)
        self.booths = []
        for row in rows:
            booth = Booth(
                id=row['id'],
                name=row['name'],
                constituency=row['constituency_name'],
                lat=float(row['lat']),
                lng=float(row['lng']),
                registered_voters=row['registered_voters'],
                throughput_rate=float(row['base_throughput']),
            )
            self.booths.append(booth)

    @property
    def tick_interval(self) -> int:
        return int(self._sim_config.get('tick_interval_seconds', 3))

    @property
    def base_arrival_rate(self) -> float:
        return float(self._sim_config.get('base_arrival_rate', 3.0))

    @property
    def minutes_per_tick(self) -> int:
        return int(self._sim_config.get('simulated_minutes_per_tick', 2))

    def get_arrival_multiplier(self) -> float:
        return self._peak_multipliers.get(self.clock.current_hour, 1.0)

    def start(self):
        """Start simulation in background thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def reset(self):
        self.clock.reset()
        self.incidents = []
        self._load_booths() # Resets queues and turnout
        self._emit_updates()

    def jump_time(self, hour: int):
        self.clock.set_time(hour, 0)
        self._emit_updates()

    def _run_loop(self):
        last_sweep_tick = 0
        while self.running and not self.clock.day_complete:
            if not self.is_paused:
                self._tick()
                
                # Proactive AI sweep every 50 ticks (~2.5 min) to conserve API quota
                if self.clock.total_ticks - last_sweep_tick >= 50:
                    self._proactive_ai_sweep()
                    last_sweep_tick = self.clock.total_ticks
                    
                self._emit_updates()
            time.sleep(self.tick_interval)

    def _proactive_ai_sweep(self):
        """Automatically triage open critical/high incidents."""
        open_criticals = [i for i in self.incidents if i.status == 'open' and i.severity in ('critical', 'high')]
        if not open_criticals:
            return
            
        from agents.incident_responder import IncidentResponderAgent
        import json as _json
        agent = IncidentResponderAgent()
        
        for inc in open_criticals[:3]:
            booth = next((b for b in self.booths if b.id == inc.booth_id), None)
            if booth:
                try:
                    raw = agent.triage_incident(inc.to_dict(), booth.to_dict())
                    # Parse result — could be dict, JSON string, or plain text
                    if isinstance(raw, dict):
                        triage_result = raw
                    elif isinstance(raw, str):
                        clean = raw.strip()
                        if clean.startswith('```'):
                            clean = clean.split('\n', 1)[-1]
                            if clean.endswith('```'):
                                clean = clean[:-3].strip()
                        try:
                            triage_result = _json.loads(clean)
                        except _json.JSONDecodeError:
                            triage_result = {'analysis': clean[:500]}
                    else:
                        triage_result = {'analysis': str(raw)[:500]}

                    inc.status = 'triaging'
                    inc.ai_recommendation = triage_result.get('analysis', 'Automatic triage complete.')
                    Database.execute_write(
                        "UPDATE incidents SET status='triaging', ai_recommendation=%s WHERE id=%s",
                        (inc.ai_recommendation, inc.id)
                    )
                    if self.socketio:
                        self.socketio.emit('agent_action', {
                            'agent': 'IncidentResponder',
                            'action': 'Auto-Triage',
                            'incident_id': inc.id,
                            'result': triage_result
                        })
                except Exception as e:
                    print(f"[AI Sweep] Error triaging {inc.id}: {e}")

    def _tick(self):
        """Execute one simulation tick."""
        self.clock.tick()
        time_multiplier = self.get_arrival_multiplier()

        for booth in self.booths:
            if not booth.is_active:
                continue

            new_queue, arrivals, departures = QueueDynamics.update_queue(
                queue_length=booth.queue_length,
                throughput_rate=booth.throughput_rate,
                base_arrival_rate=self.base_arrival_rate,
                minutes_per_tick=self.minutes_per_tick,
                time_multiplier=time_multiplier,
                is_polling_active=self.clock.is_polling_active,
                evm_status=booth.evm_status,
            )
            booth.queue_length = new_queue
            booth.total_votes_cast += departures

            # Check for new incidents
            if self.clock.is_polling_active:
                new_incidents = self.incident_injector.check_for_incidents(
                    booth, self.clock.current_hour
                )
                for inc in new_incidents:
                    self.incidents.append(inc)
                    self.incident_tick_map[inc.id] = self.clock.total_ticks
                    booth.incidents.append(inc.id)
                    # Persist to DB
                    self._save_incident(inc)
                    if self.socketio:
                        self.socketio.emit('new_incident', inc.to_dict())

        self._auto_resolve_incidents()

        # Record turnout every 5 ticks
        if self.clock.total_ticks % 5 == 0:
            self._record_turnout()

    def _save_incident(self, inc: Incident):
        """Persist incident to MySQL."""
        try:
            Database.execute_write(
                """INSERT INTO incidents (id, booth_id, incident_type, severity, description, status, reported_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (inc.id, inc.booth_id, inc.incident_type, inc.severity, inc.description, inc.status, inc.reported_at)
            )
        except Exception:
            pass  # Don't crash simulation on DB error

    def _auto_resolve_incidents(self):
        for inc in self.incidents:
            if inc.status not in ('open', 'triaging'):
                continue
            created_tick = self.incident_tick_map.get(inc.id, 0)
            ticks_elapsed = self.clock.total_ticks - created_tick
            if IncidentInjector.auto_resolve_check(inc.severity, ticks_elapsed):
                inc.status = 'resolved'
                inc.resolved_at = datetime.now().isoformat()
                inc.resolution_notes = 'Auto-resolved by system'
                try:
                    Database.execute_write(
                        "UPDATE incidents SET status='resolved', resolved_at=NOW() WHERE id=%s",
                        (inc.id,)
                    )
                except Exception:
                    pass
                for booth in self.booths:
                    if booth.id == inc.booth_id:
                        if inc.incident_type == 'EVM_MALFUNCTION':
                            booth.evm_status = 'replaced'
                        elif inc.incident_type == 'VVPAT_JAM':
                            booth.vvpat_status = 'replaced'
                        elif inc.incident_type == 'POWER_OUTAGE':
                            booth.evm_status = 'operational'
                        break

    def _record_turnout(self):
        total_votes = sum(b.total_votes_cast for b in self.booths)
        total_registered = sum(b.registered_voters for b in self.booths)
        avg_queue = sum(b.queue_length for b in self.booths) / max(len(self.booths), 1)
        open_incidents = sum(1 for i in self.incidents if i.status == 'open')
        turnout_pct = round((total_votes / max(total_registered, 1)) * 100, 2)

        snapshot = {
            'time': self.clock.get_time_string(),
            'tick': self.clock.total_ticks,
            'total_votes': total_votes,
            'turnout_percent': turnout_pct,
        }
        self.turnout_history.append(snapshot)

        try:
            Database.execute_write(
                """INSERT INTO turnout_snapshots (tick, sim_time, phase, total_votes, total_registered, turnout_percent, avg_queue_length, open_incidents)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (self.clock.total_ticks, self.clock.get_time_string(), self.clock.phase,
                 total_votes, total_registered, turnout_pct, round(avg_queue, 1), open_incidents)
            )
        except Exception:
            pass

    def _emit_updates(self):
        stats = self.get_stats()
        self.socketio.emit('stats_update', stats)
        top_booths = sorted(self.booths, key=lambda b: b.queue_length, reverse=True)[:20]
        self.socketio.emit('booth_update', {
            'booths': [b.to_dict() for b in top_booths],
            'clock': self.clock.to_dict(),
        })

    # ── Public API ──

    def get_stats(self) -> dict:
        total_votes = sum(b.total_votes_cast for b in self.booths)
        total_registered = sum(b.registered_voters for b in self.booths)
        avg_queue = sum(b.queue_length for b in self.booths) / max(len(self.booths), 1)
        open_incidents = sum(1 for i in self.incidents if i.status == 'open')
        critical = sum(1 for i in self.incidents if i.status == 'open' and i.severity == 'critical')
        return {
            'total_votes': total_votes,
            'total_registered': total_registered,
            'turnout_percent': round((total_votes / max(total_registered, 1)) * 100, 2),
            'active_booths': sum(1 for b in self.booths if b.is_active),
            'total_booths': len(self.booths),
            'avg_queue_length': round(avg_queue, 1),
            'max_queue_length': max((b.queue_length for b in self.booths), default=0),
            'open_incidents': open_incidents,
            'critical_incidents': critical,
            'total_incidents': len(self.incidents),
            'clock': self.clock.to_dict(),
        }

    def get_all_booths(self, constituency: str = None) -> list[dict]:
        booths = self.booths
        if constituency:
            booths = [b for b in booths if b.constituency == constituency]
        return [b.to_dict() for b in booths]

    def get_booth(self, booth_id: str) -> dict | None:
        for b in self.booths:
            if b.id == booth_id:
                return b.to_dict()
        return None

    def get_incidents(self, status: str = None, severity: str = None) -> list[dict]:
        result = self.incidents
        if status:
            result = [i for i in result if i.status == status]
        if severity:
            result = [i for i in result if i.severity == severity]
        return [i.to_dict() for i in sorted(result, key=lambda x: x.reported_at, reverse=True)]

    def get_incident(self, incident_id: str) -> Incident | None:
        for i in self.incidents:
            if i.id == incident_id:
                return i
        return None

    def report_incident(self, booth_id: str, description: str) -> Incident | None:
        booth = next((b for b in self.booths if b.id == booth_id), None)
        if not booth:
            return None
        inc = Incident(
            booth_id=booth.id, booth_name=booth.name, constituency=booth.constituency,
            incident_type='VOTER_ID_DISPUTE', severity='medium',
            description=description, status='open',
        )
        self.incidents.append(inc)
        self.incident_tick_map[inc.id] = self.clock.total_ticks
        booth.incidents.append(inc.id)
        self._save_incident(inc)
        if self.socketio:
            self.socketio.emit('new_incident', inc.to_dict())
        return inc
