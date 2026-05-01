"""
ElectaVerse — Content Routes (Timeline + Voter Guide)
Serves all content from MySQL. RBAC-filtered by authenticated user's role.
"""

import json
from flask import Blueprint, request, jsonify
from db.connection import Database
from routes.auth_routes import _get_user_by_token

content_bp = Blueprint('content', __name__)

# Engine reference — set via init_app()
_engine = None

def init_app(engine):
    global _engine
    _engine = engine


def _get_current_user():
    """Extract authenticated user from request. Returns (user_dict, role_str)."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = _get_user_by_token(token)
    if not user:
        return None, None
    return user, user.get('role', 'voter')


# ═══════════════════════════════════════════════════
# ELECTION TIMELINE
# ═══════════════════════════════════════════════════

@content_bp.route('/api/content/timeline', methods=['GET'])
def get_timeline():
    """Return all election phases from DB, with role-specific actions."""
    user, role = _get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    rows = Database.execute(
        "SELECT * FROM election_phases ORDER BY display_order ASC"
    )

    phases = []
    for row in rows:
        # Parse JSON fields
        key_activities = json.loads(row['key_activities']) if isinstance(row['key_activities'], str) else row['key_activities']
        all_role_actions = json.loads(row['role_actions']) if isinstance(row['role_actions'], str) else row['role_actions']

        # RBAC: include only the current user's role actions + always include voter (base)
        my_actions = all_role_actions.get(role, all_role_actions.get('voter', []))

        phase = {
            'id': row['id'],
            'phase_key': row['phase_key'],
            'title': row['title'],
            'description': row['description'],
            'icon': row['icon'],
            'start_label': row['start_label'],
            'end_label': row['end_label'],
            'duration_info': row['duration_info'],
            'key_activities': key_activities,
            'my_actions': my_actions,
            'display_order': row['display_order'],
        }

        # Officials and observers also see all roles for reference
        if role in ('official', 'observer'):
            phase['all_role_actions'] = all_role_actions

        phases.append(phase)

    return jsonify({
        'phases': phases,
        'user_role': role,
        'total': len(phases),
    })


@content_bp.route('/api/content/timeline/<int:phase_id>/ask-ai', methods=['POST'])
def ask_ai_about_phase(phase_id):
    """Ask AI a question about a specific election phase."""
    user, role = _get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question is required'}), 400

    # Fetch phase from DB
    row = Database.execute_one("SELECT * FROM election_phases WHERE id = %s", (phase_id,))
    if not row:
        return jsonify({'error': 'Phase not found'}), 404

    # Parse JSON
    phase_data = {
        'title': row['title'],
        'description': row['description'],
        'duration_info': row['duration_info'],
        'key_activities': json.loads(row['key_activities']) if isinstance(row['key_activities'], str) else row['key_activities'],
    }

    from agents.election_analyst import ElectionAnalystAgent
    agent = ElectionAnalystAgent()
    answer = agent.answer_phase_question(phase_data, question, role)

    return jsonify({
        'question': question,
        'answer': answer,
        'phase_id': phase_id,
        'phase_title': row['title'],
        'agent': 'ElectionAnalyst',
        'user_role': role,
    })


# ═══════════════════════════════════════════════════
# VOTER GUIDE
# ═══════════════════════════════════════════════════

@content_bp.route('/api/content/voter-guide', methods=['GET'])
def get_voter_guide():
    """Return all voter guide steps from DB, with role-specific notes."""
    user, role = _get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    rows = Database.execute(
        "SELECT * FROM voter_guide_steps ORDER BY display_order ASC"
    )

    steps = []
    for row in rows:
        docs = json.loads(row['documents_required']) if isinstance(row['documents_required'], str) else (row['documents_required'] or [])
        tips = json.loads(row['tips']) if isinstance(row['tips'], str) else (row['tips'] or [])
        all_notes = json.loads(row['role_specific_notes']) if isinstance(row['role_specific_notes'], str) else row['role_specific_notes']

        # RBAC: serve only the note for this user's role
        my_note = all_notes.get(role, all_notes.get('voter', ''))

        step = {
            'id': row['id'],
            'step_number': row['step_number'],
            'title': row['title'],
            'description': row['description'],
            'icon': row['icon'],
            'documents_required': docs,
            'tips': tips,
            'my_note': my_note,
            'sim_phase_link': row['sim_phase_link'],
            'display_order': row['display_order'],
        }

        # Officials and observers see all role notes for reference
        if role in ('official', 'observer'):
            step['all_role_notes'] = all_notes

        steps.append(step)

    response_data = {
        'steps': steps,
        'user_role': role,
        'total': len(steps),
    }

    # Location-Based Live Context: Assign a booth based on user's constituency
    if user.get('constituency_id') and _engine:
        # Find booths in their constituency
        local_booths = [b for b in _engine.booths if b.constituency_id == user['constituency_id']]
        if local_booths:
            # Deterministically assign a booth based on user ID
            assigned_booth = local_booths[user['id'] % len(local_booths)]
            
            # Find any open incidents for this booth
            booth_incidents = [i for i in _engine.incidents if i.booth_id == assigned_booth.id and i.status != 'resolved']
            
            response_data['assigned_booth'] = {
                'id': assigned_booth.id,
                'name': assigned_booth.name,
                'constituency_id': assigned_booth.constituency_id,
                'queue_length': assigned_booth.queue_length,
                'evm_status': assigned_booth.evm_status,
                'open_incidents_count': len(booth_incidents)
            }

    return jsonify(response_data)


@content_bp.route('/api/content/voter-guide/<int:step_id>/ask-ai', methods=['POST'])
def ask_ai_about_step(step_id):
    """Ask AI a question about a specific voter guide step."""
    user, role = _get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'Question is required'}), 400

    row = Database.execute_one("SELECT * FROM voter_guide_steps WHERE id = %s", (step_id,))
    if not row:
        return jsonify({'error': 'Step not found'}), 404

    step_data = {
        'step_number': row['step_number'],
        'title': row['title'],
        'description': row['description'],
        'documents_required': json.loads(row['documents_required']) if isinstance(row['documents_required'], str) else (row['documents_required'] or []),
        'tips': json.loads(row['tips']) if isinstance(row['tips'], str) else (row['tips'] or []),
    }

    from agents.election_analyst import ElectionAnalystAgent
    agent = ElectionAnalystAgent()
    answer = agent.answer_guide_question(step_data, question, role)

    return jsonify({
        'question': question,
        'answer': answer,
        'step_id': step_id,
        'step_title': row['title'],
        'agent': 'ElectionAnalyst',
        'user_role': role,
    })


# ═══════════════════════════════════════════════════
# AI FACT CHECKER
# ═══════════════════════════════════════════════════

@content_bp.route('/api/content/fact-check', methods=['POST'])
def fact_check_claim():
    """Verify a user claim using the FactCheckerAgent."""
    user, role = _get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    claim = data.get('claim', '').strip()
    if not claim:
        return jsonify({'error': 'Claim is required'}), 400

    # Get live context if engine is available
    live_context = None
    if _engine:
        live_context = _engine.get_stats()

    from agents.fact_checker import FactCheckerAgent
    agent = FactCheckerAgent()
    
    result = agent.verify_claim(claim, live_context)
    
    return jsonify({
        'claim': claim,
        'verdict': result.get('verdict', 'ERROR'),
        'confidence_score': result.get('confidence_score', 0),
        'reasoning': result.get('reasoning', 'Analysis failed.'),
        'official_sources': result.get('official_sources', [])
    })

# ═══════════════════════════════════════════════════
# VOTER IQ QUIZ
# ═══════════════════════════════════════════════════

QUIZ_BANK = [
    {
        "id": 1,
        "question": "What is the minimum voting age in India?",
        "options": ["16 years", "18 years", "21 years", "25 years"],
        "correct_index": 1,
        "explanation": "The 61st Amendment Act (1988) lowered the voting age from 21 to 18 years."
    },
    {
        "id": 2,
        "question": "What is the maximum allowed distance for a voter to travel to a polling booth?",
        "options": ["1 km", "2 km", "5 km", "10 km"],
        "correct_index": 1,
        "explanation": "ECI guidelines mandate that a polling station should be set up within 2 km of every voter's residence."
    },
    {
        "id": 3,
        "question": "What does VVPAT stand for?",
        "options": ["Voter Verification Paper Audit Trail", "Voter Verifiable Paper Audit Trail", "Voting Verification Print Audit Trail", "Valid Vote Paper Audit Trail"],
        "correct_index": 1,
        "explanation": "Voter Verifiable Paper Audit Trail allows voters to verify that their vote was cast correctly."
    },
    {
        "id": 4,
        "question": "Can you vote if you are in the queue at the polling booth exactly at the closing time (e.g., 6:00 PM)?",
        "options": ["No, doors close exactly at 6", "Yes, everyone in line at 6 PM gets a slip to vote", "Only if the Presiding Officer allows", "Only senior citizens"],
        "correct_index": 1,
        "explanation": "If you join the queue before the official closing time, you will be issued a slip and allowed to vote, no matter how long it takes."
    },
    {
        "id": 5,
        "question": "Is it mandatory to have a Voter ID card (EPIC) to cast your vote?",
        "options": ["Yes, strictly mandatory", "No, other approved IDs like Aadhar or Passport are accepted", "Only for state elections", "No, verbal confirmation is enough"],
        "correct_index": 1,
        "explanation": "While EPIC is preferred, the ECI accepts several other alternative photo identity documents like Aadhar, PAN, Driving License, etc., provided your name is on the electoral roll."
    }
]

@content_bp.route('/api/quiz/questions', methods=['GET'])
def get_quiz_questions():
    """Return 5 questions for the Voter IQ module."""
    # We could randomize from a larger bank, but for the demo we return these 5
    return jsonify({
        'questions': QUIZ_BANK
    })
