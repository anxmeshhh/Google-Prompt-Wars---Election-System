"""
ElectaVerse — Master Simulation Engine
Runs the real-time election day simulation in a background thread.
"""

import time
import random
import threading
from datetime import datetime
from simulation.election_clock import ElectionClock
from simulation.queue_dynamics import QueueDynamics
from simulation.incident_injector import IncidentInjector
from models.booth import Booth, create_booth
from models.incident import Incident
from config import SimulationConfig


class SimulationEngine:
    """Master simulation controller — runs in a background thread."""

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.clock = ElectionClock()
        self.incident_injector = IncidentInjector()
        self.booths: list[Booth] = []
        self.incidents: list[Incident] = []
        self.incident_tick_map: dict[str, int] = {}
        self.turnout_history: list[dict] = []
        self.running = False
        self._thread = None
        self._initialize_booths()

    def _initialize_booths(self):
        """Create all booths across constituencies."""
        booth_index = 0
        for constituency in SimulationConfig.CONSTITUENCIES:
            for i in range(SimulationConfig.BOOTHS_PER_CONSTITUENCY):
                booth_index += 1
                booth = create_booth(booth_index, constituency)
                self.booths.append(booth)

    def start(self):
        """Start the simulation in a background thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the simulation."""
        self.running = False

    def _run_loop(self):
        """Main simulation loop."""
        while self.running and not self.clock.day_complete:
            self._tick()
            if self.socketio:
                self._emit_updates()
            time.sleep(SimulationConfig.TICK_INTERVAL_SECONDS)

    def _tick(self):
        """Execute one simulation tick."""
        self.clock.tick()
        time_multiplier = self.clock.get_arrival_multiplier()

        for booth in self.booths:
            if not booth.is_active:
                continue

            # Update queue dynamics
            new_queue, arrivals, departures = QueueDynamics.update_queue(
                queue_length=booth.queue_length,
                throughput_rate=booth.throughput_rate,
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
                    if self.socketio:
                        self.socketio.emit('new_incident', inc.to_dict())

        # Auto-resolve old incidents
        self._auto_resolve_incidents()

        # Record turnout snapshot
        if self.clock.total_ticks % 5 == 0:
            self._record_turnout()

    def _auto_resolve_incidents(self):
        """Auto-resolve incidents that have been open long enough."""
        for inc in self.incidents:
            if inc.status != 'open' and inc.status != 'triaging':
                continue
            created_tick = self.incident_tick_map.get(inc.id, 0)
            ticks_elapsed = self.clock.total_ticks - created_tick
            if IncidentInjector.auto_resolve_check(inc, ticks_elapsed):
                inc.status = 'resolved'
                inc.resolved_at = datetime.now().isoformat()
                inc.resolution_notes = 'Auto-resolved by system'
                # Restore booth status
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
        """Record a turnout snapshot for analytics."""
        total_votes = sum(b.total_votes_cast for b in self.booths)
        total_registered = sum(b.registered_voters for b in self.booths)
        self.turnout_history.append({
            'time': self.clock.get_time_string(),
            'tick': self.clock.total_ticks,
            'total_votes': total_votes,
            'turnout_percent': round((total_votes / max(total_registered, 1)) * 100, 2),
        })

    def _emit_updates(self):
        """Push real-time data to all connected clients via WebSocket."""
        stats = self.get_stats()
        # Emit only summary + changed booths to reduce bandwidth
        self.socketio.emit('stats_update', stats)
        # Send top 20 most active booths (sorted by queue length)
        top_booths = sorted(self.booths, key=lambda b: b.queue_length, reverse=True)[:20]
        self.socketio.emit('booth_update', {
            'booths': [b.to_dict() for b in top_booths],
            'clock': self.clock.to_dict(),
        })

    def get_stats(self) -> dict:
        """Get aggregate statistics."""
        total_votes = sum(b.total_votes_cast for b in self.booths)
        total_registered = sum(b.registered_voters for b in self.booths)
        active_booths = sum(1 for b in self.booths if b.is_active)
        avg_queue = sum(b.queue_length for b in self.booths) / max(len(self.booths), 1)
        open_incidents = sum(1 for i in self.incidents if i.status == 'open')
        critical_incidents = sum(1 for i in self.incidents if i.status == 'open' and i.severity == 'critical')

        return {
            'total_votes': total_votes,
            'total_registered': total_registered,
            'turnout_percent': round((total_votes / max(total_registered, 1)) * 100, 2),
            'active_booths': active_booths,
            'total_booths': len(self.booths),
            'avg_queue_length': round(avg_queue, 1),
            'max_queue_length': max((b.queue_length for b in self.booths), default=0),
            'open_incidents': open_incidents,
            'critical_incidents': critical_incidents,
            'total_incidents': len(self.incidents),
            'clock': self.clock.to_dict(),
        }

    def get_all_booths(self, constituency: str = None) -> list[dict]:
        """Get all booth states, optionally filtered."""
        booths = self.booths
        if constituency:
            booths = [b for b in booths if b.constituency == constituency]
        return [b.to_dict() for b in booths]

    def get_booth(self, booth_id: str) -> dict | None:
        """Get a single booth by ID."""
        for b in self.booths:
            if b.id == booth_id:
                return b.to_dict()
        return None

    def get_incidents(self, status: str = None, severity: str = None) -> list[dict]:
        """Get incidents, optionally filtered."""
        result = self.incidents
        if status:
            result = [i for i in result if i.status == status]
        if severity:
            result = [i for i in result if i.severity == severity]
        return [i.to_dict() for i in sorted(result, key=lambda x: x.reported_at, reverse=True)]

    def get_incident(self, incident_id: str) -> Incident | None:
        """Get a single incident by ID."""
        for i in self.incidents:
            if i.id == incident_id:
                return i
        return None

    def report_incident(self, booth_id: str, description: str) -> Incident | None:
        """Manually report a new incident."""
        booth = None
        for b in self.booths:
            if b.id == booth_id:
                booth = b
                break
        if not booth:
            return None
        inc = Incident(
            booth_id=booth.id,
            booth_name=booth.name,
            constituency=booth.constituency,
            incident_type='VOTER_ID_DISPUTE',
            severity='medium',
            description=description,
            status='open',
        )
        self.incidents.append(inc)
        self.incident_tick_map[inc.id] = self.clock.total_ticks
        booth.incidents.append(inc.id)
        if self.socketio:
            self.socketio.emit('new_incident', inc.to_dict())
        return inc
