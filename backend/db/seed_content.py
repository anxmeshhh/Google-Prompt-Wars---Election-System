"""
ElectaVerse — Seed Election Timeline + Voter Guide into MySQL
All content drawn from ECI (Election Commission of India) official processes.
Run: python db/seed_content.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import Database

ELECTION_PHASES = [
    {
        "phase_key": "ANNOUNCEMENT",
        "title": "Election Announcement",
        "description": "The Election Commission of India (ECI) announces the election schedule, including dates for nominations, scrutiny, withdrawal, and polling. The Model Code of Conduct (MCC) comes into immediate effect, restricting government announcements, transfers, and new schemes.",
        "icon": "📢",
        "start_label": "ECI Notification",
        "end_label": "Nomination Start",
        "duration_info": "1–2 weeks before nominations open",
        "key_activities": [
            "ECI holds press conference announcing schedule",
            "Model Code of Conduct (MCC) takes effect immediately",
            "Government halts new policy announcements and transfers",
            "Political parties begin strategizing and candidate selection",
            "Electoral rolls are finalized and published",
            "Security deployment planning begins"
        ],
        "role_actions": {
            "voter": [
                "Verify your name on the electoral roll at nvsp.in",
                "Check your assigned polling booth number",
                "Ensure your Voter ID (EPIC) card is valid and up to date",
                "Download the Voter Helpline App for updates"
            ],
            "official": [
                "Acknowledge MCC enforcement — halt discretionary spending",
                "Prepare booth infrastructure and logistics inventory",
                "Submit booth officer staffing requirements to DEO",
                "Verify EVM and VVPAT machine availability per booth"
            ],
            "observer": [
                "Register as an election observer with the ECI if applicable",
                "Monitor MCC compliance by political parties and incumbents",
                "Note any pre-announcement policy rushes by government",
                "Prepare monitoring checklists aligned with ECI observer guidelines"
            ]
        },
        "display_order": 1
    },
    {
        "phase_key": "NOMINATION",
        "title": "Nomination & Scrutiny",
        "description": "Candidates file their nomination papers with the Returning Officer (RO). Each nomination includes an affidavit disclosing criminal history, assets, liabilities, and educational qualifications. The RO scrutinizes nominations for validity, and candidates may withdraw within the allowed window.",
        "icon": "📝",
        "start_label": "Filing Opens",
        "end_label": "Final Candidate List",
        "duration_info": "7–10 days (filing + scrutiny + withdrawal)",
        "key_activities": [
            "Candidates file nominations with the Returning Officer",
            "Mandatory affidavits: criminal record, assets, education",
            "Returning Officer scrutinizes all nominations within 1 day",
            "Invalid nominations rejected (incomplete forms, missing deposits)",
            "2-day withdrawal window after scrutiny",
            "Final list of contesting candidates published"
        ],
        "role_actions": {
            "voter": [
                "Research candidates' criminal and financial backgrounds via ADR/MyNeta",
                "Read affidavits published on the ECI website",
                "Attend public debates or town halls if organized",
                "Evaluate party manifestos released during this period"
            ],
            "official": [
                "Process nomination forms and verify supporting documents",
                "Conduct scrutiny within statutory 1-day deadline",
                "Publish accepted/rejected nomination lists publicly",
                "Allocate election symbols to independent candidates"
            ],
            "observer": [
                "Verify that nomination scrutiny is conducted impartially",
                "Check if affidavit disclosures are complete and accurate",
                "Monitor for coercion or inducement in candidate withdrawals",
                "Document symbol allocation fairness for independents"
            ]
        },
        "display_order": 2
    },
    {
        "phase_key": "CAMPAIGN",
        "title": "Election Campaign",
        "description": "Political parties and candidates conduct rallies, door-to-door campaigns, social media outreach, and media advertising. Expenditure limits are enforced by the ECI. Campaigning must stop 48 hours before polling (the 'silence period') to allow voters to reflect without influence.",
        "icon": "📣",
        "start_label": "Campaign Begins",
        "end_label": "48hrs Before Polling",
        "duration_info": "2–4 weeks, ends 48 hours before poll day",
        "key_activities": [
            "Political rallies, roadshows, and public meetings",
            "TV debates, newspaper ads, social media campaigns",
            "Door-to-door canvassing by party workers",
            "ECI monitors campaign expenditure (₹95 lakh limit for Lok Sabha)",
            "MCMC (Media Certification & Monitoring Committee) reviews all ads",
            "Campaign silence period: 48 hours before polling"
        ],
        "role_actions": {
            "voter": [
                "Attend rallies or watch debates to understand candidate positions",
                "Verify claims made in campaign speeches using credible sources",
                "Report MCC violations via the cVIGIL app",
                "Avoid sharing unverified election news on social media"
            ],
            "official": [
                "Monitor campaign expenditure of all candidates",
                "Enforce MCC — no hate speech, no religious/caste appeals",
                "Process permission requests for rallies and public meetings",
                "Coordinate with law enforcement for rally security"
            ],
            "observer": [
                "Track MCC violations and report to the ECI Observer portal",
                "Monitor paid news and undisclosed political advertising",
                "Verify expenditure returns filed by candidates are accurate",
                "Document instances of voter inducement (cash, liquor, gifts)"
            ]
        },
        "display_order": 3
    },
    {
        "phase_key": "ACTIVE_POLLING",
        "title": "Polling Day",
        "description": "Voters cast their ballots at assigned polling stations using Electronic Voting Machines (EVMs) with Voter Verifiable Paper Audit Trail (VVPAT). Booths operate from 7 AM to 6 PM. Each voter is identified, marked with indelible ink, and casts a secret ballot. This is the phase where ElectaVerse's real-time monitoring is most active.",
        "icon": "🗳️",
        "start_label": "7:00 AM",
        "end_label": "6:00 PM",
        "duration_info": "One day (7 AM – 6 PM, voters in queue by 6 PM can vote)",
        "key_activities": [
            "Voters arrive at assigned booth with valid ID",
            "Identity verified, name checked on electoral roll",
            "Indelible ink applied to left index finger",
            "Vote cast on EVM, VVPAT slip verified by voter for 7 seconds",
            "Booth agents from political parties monitor process",
            "Real-time incident reporting and queue management"
        ],
        "role_actions": {
            "voter": [
                "Arrive at your assigned booth with Voter ID or approved alternative ID",
                "Queue patiently — ElectaVerse shows real-time wait estimates",
                "Verify the VVPAT slip matches your chosen candidate",
                "Report any irregularity to the Presiding Officer immediately",
                "Do NOT share photos/videos from inside the booth (illegal)"
            ],
            "official": [
                "Ensure booth setup complete by 6:30 AM: EVMs, VVPAT, furniture, signage",
                "Verify mock poll on EVM before actual voting starts",
                "Manage queue flow — deploy queue managers at high-traffic booths",
                "Handle EVM/VVPAT malfunctions per ECI SOP (replace within 30 min)",
                "Report hourly turnout to the Returning Officer"
            ],
            "observer": [
                "Verify that mock poll is conducted correctly with party agents present",
                "Monitor voter identification process for irregularities",
                "Check that VVPAT is operational and slips are visible to voters",
                "Document any booth capture attempts or voter intimidation",
                "Ensure accessibility provisions for disabled and elderly voters"
            ]
        },
        "display_order": 4
    },
    {
        "phase_key": "POST_POLL",
        "title": "Post-Polling & Sealing",
        "description": "After the last voter casts their ballot, EVMs are sealed in the presence of candidates' agents. The sealed machines are transported under armed escort to a central strong room. The strong room is secured with multi-layer locks, 24/7 CCTV surveillance, and round-the-clock paramilitary guard until counting day.",
        "icon": "🔒",
        "start_label": "Booth Closing",
        "end_label": "Strong Room Sealed",
        "duration_info": "Same evening, may extend to next morning",
        "key_activities": [
            "Final voter count reconciled with EVM readings",
            "EVMs sealed with unique serial-numbered tags",
            "Party agents apply their own seals on EVM cases",
            "Sealed EVMs transported to strong room under armed escort",
            "Strong room sealed with multi-layer lock system",
            "24/7 CCTV and paramilitary guard deployed at strong room"
        ],
        "role_actions": {
            "voter": [
                "Your role is complete — thank you for participating in democracy",
                "Wait for counting day for results (usually 3–5 days after polling)",
                "Report any post-poll irregularities you witnessed to authorities",
                "Discuss your experience — encourage others to vote next time"
            ],
            "official": [
                "Reconcile voter turnout with EVM vote count — document discrepancies",
                "Seal all EVMs in presence of polling agents — obtain signatures",
                "Escort sealed machines to strong room with security personnel",
                "Submit Form 17C (Account of Votes Recorded) to Returning Officer"
            ],
            "observer": [
                "Witness and verify the EVM sealing process at each booth",
                "Confirm that candidate agents' seals are applied correctly",
                "Monitor strong room security arrangements",
                "File observer report with the ECI within 24 hours"
            ]
        },
        "display_order": 5
    },
    {
        "phase_key": "COUNTING",
        "title": "Counting & Results",
        "description": "Counting occurs at designated centers under heavy security. EVMs are opened round-by-round, with results tallied on a whiteboard visible to agents. VVPAT paper slips from randomly selected 5 booths per constituency are matched against EVM counts for verification. Results are announced progressively and the winning candidate receives a certificate of election.",
        "icon": "📊",
        "start_label": "Counting Begins",
        "end_label": "Results Declared",
        "duration_info": "1 day (usually 3–5 days after polling)",
        "key_activities": [
            "Strong room seals verified in presence of candidates/agents",
            "EVMs opened round by round (each round = 14 tables = 14 booths)",
            "Postal ballots counted first before EVM counting begins",
            "VVPAT verification: random 5 booths per constituency paper-matched",
            "Results displayed on central result board, updated every round",
            "Returning Officer declares final result and issues certificate"
        ],
        "role_actions": {
            "voter": [
                "Follow live results on ECI's results portal or ElectaVerse",
                "Understand the round-by-round counting process",
                "Accept the democratic outcome regardless of result",
                "Report any result-related misinformation you encounter"
            ],
            "official": [
                "Verify strong room seals are intact before opening",
                "Conduct counting as per ECI's round-wise protocol",
                "Handle recounting requests if margin is narrow (per rules)",
                "Issue certificate of election to the winning candidate"
            ],
            "observer": [
                "Verify that strong room seals are intact and tamper-free",
                "Monitor VVPAT paper count verification against EVM totals",
                "Document any discrepancies between rounds and report to ECI",
                "Ensure transparency of the counting process to all agents present"
            ]
        },
        "display_order": 6
    }
]

VOTER_GUIDE_STEPS = [
    {
        "step_number": 1,
        "title": "Check Your Registration",
        "description": "Before election day, verify that your name appears on the electoral roll for your constituency. You can check online via the National Voter's Service Portal (NVSP) at nvsp.in, through the Voter Helpline App, or by visiting your nearest Electoral Registration Officer. If your name is missing, you can apply for inclusion using Form 6.",
        "icon": "🔍",
        "documents_required": [
            "Voter ID Card (EPIC) — primary identification",
            "Aadhaar Card — for address verification",
            "Passport — alternative photo ID",
            "Driving License — alternative photo ID",
            "PAN Card — alternative photo ID",
            "Any government-issued photo ID"
        ],
        "tips": [
            "Check your name at least 2 weeks before election day to allow time for corrections",
            "Use the Voter Helpline App (available on Android/iOS) for instant status checks",
            "Note down your Polling Station number and name — you'll need it on election day",
            "If you've moved, apply for transfer using Form 6A at your new constituency office"
        ],
        "role_specific_notes": {
            "voter": "Make sure your photo on the EPIC card is recognizable. If it's too old or unclear, apply for a replacement at your ERO office — carry two passport-size photos.",
            "official": "As a Booth Level Officer (BLO), conduct door-to-door verification of the draft electoral roll. Update entries using Form 6, 7, 8, and 8A as applicable. Ensure no duplicate entries exist.",
            "observer": "Verify that the electoral roll revision process followed the ECI's schedule. Check for mass deletions or additions near the deadline that could indicate manipulation."
        },
        "sim_phase_link": "ANNOUNCEMENT",
        "display_order": 1
    },
    {
        "step_number": 2,
        "title": "Prepare for Polling Day",
        "description": "Gather your identification documents, locate your assigned polling station, and plan your travel route. Note the polling hours (typically 7 AM – 6 PM). Wear comfortable clothes and carry water — queues can be long. You do NOT need to carry your Voter ID if you have any other approved photo ID.",
        "icon": "📋",
        "documents_required": [
            "Voter ID Card (EPIC) — most common",
            "Aadhaar Card",
            "Passport",
            "Driving License",
            "PAN Card",
            "MNREGA Job Card",
            "Health Insurance Smart Card (RSBY)",
            "Bank/Post Office Passbook with Photo",
            "Any government photo ID with name and photo"
        ],
        "tips": [
            "Carry ANY ONE approved photo ID — you don't need multiple documents",
            "Find your exact booth via the Voter Helpline App or nvsp.in",
            "Plan to arrive early morning (7–9 AM) or late afternoon (4–6 PM) to avoid peak crowds",
            "Wear long-sleeve clothing if you want to cover the ink mark afterward",
            "Election day is a paid holiday — inform your employer if needed"
        ],
        "role_specific_notes": {
            "voter": "ElectaVerse's real-time queue data can help you pick the best time to visit your booth. Check the Live Ops tab on polling day for real-time wait times at your assigned station.",
            "official": "Complete booth setup checklist by 6:30 AM: EVM placement, VVPAT setup, voter register, ink, signage, seating for agents, accessibility ramp. Run mandatory mock poll with all party agents present.",
            "observer": "Arrive before booth opens (6:30 AM) to witness the mock poll. Verify that the EVM shows zero votes before polling starts. Check accessibility provisions for disabled voters."
        },
        "sim_phase_link": "CAMPAIGN",
        "display_order": 2
    },
    {
        "step_number": 3,
        "title": "Cast Your Vote",
        "description": "At the polling station: join the queue, present your photo ID to the polling officer, get your name verified on the electoral roll, receive indelible ink mark on your left index finger, proceed to the voting compartment, press the button on the EVM next to your chosen candidate's name and symbol, verify the VVPAT slip displays for 7 seconds, and exit. The entire process takes 2–3 minutes inside the booth.",
        "icon": "🗳️",
        "documents_required": [
            "Any ONE approved photo ID from the list above"
        ],
        "tips": [
            "The EVM has candidate names, party symbols, and a blue button next to each — press firmly",
            "After pressing the button, a beep confirms your vote and the VVPAT slip shows for 7 seconds",
            "Verify that the VVPAT slip shows the correct candidate name and symbol",
            "If the VVPAT slip is wrong, immediately alert the Presiding Officer — you have the right to a test vote",
            "Do NOT carry your phone into the voting compartment — it's a punishable offense",
            "Photography inside the booth is strictly prohibited under Section 128 of the RP Act"
        ],
        "role_specific_notes": {
            "voter": "Take your time. No one is allowed to rush you. If you make a mistake or the EVM malfunctions, tell the Presiding Officer — you will be given a fresh ballot via the tendered vote process.",
            "official": "Ensure one voter enters the compartment at a time. Monitor VVPAT paper stock. If EVM fails, follow the replacement SOP: seal the faulty unit, deploy backup, document everything on Form 17C.",
            "observer": "Monitor that voter secrecy is maintained in the voting compartment. Ensure indelible ink is being applied correctly. Watch for booth capture signs: mass entries, intimidation, or agent interference."
        },
        "sim_phase_link": "ACTIVE_POLLING",
        "display_order": 3
    },
    {
        "step_number": 4,
        "title": "After Voting",
        "description": "After casting your vote, exit the polling station. The indelible ink mark on your finger prevents duplicate voting and will fade in 2–4 weeks. You can track election results on the ECI website or ElectaVerse's Live Ops dashboard on counting day. Encourage friends and family to vote — higher turnout strengthens democracy.",
        "icon": "✅",
        "documents_required": [],
        "tips": [
            "Show your inked finger proudly — it's a symbol of democratic participation",
            "Share your voting experience (without revealing who you voted for)",
            "Report any irregularities you witnessed to the ECI via cVIGIL app",
            "Follow counting day results on ElectaVerse for real-time updates",
            "Remember: your vote is secret and protected by law — never share it"
        ],
        "role_specific_notes": {
            "voter": "Congratulations on participating in the world's largest democracy! Every vote matters. If you faced any issues, file a complaint via the Voter Helpline App (1950) for ECI's records.",
            "official": "After the last voter, seal the EVM in the presence of all party agents. Complete Form 17C — Account of Votes Recorded. Transport sealed EVMs to the strong room under armed escort.",
            "observer": "File your observer report within 24 hours. Document total voter turnout, incidents, EVM replacements, accessibility compliance, and any MCC violations observed. Submit via the ECI Observer Portal."
        },
        "sim_phase_link": "POST_POLL",
        "display_order": 4
    }
]


def seed_content():
    """Seed election timeline and voter guide data into MySQL."""
    Database.initialize()

    # Create tables if not exist
    print("Creating content tables...")
    Database.execute_write("""
        CREATE TABLE IF NOT EXISTS election_phases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phase_key VARCHAR(30) NOT NULL UNIQUE,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            icon VARCHAR(10) NOT NULL DEFAULT '📋',
            start_label VARCHAR(50) NOT NULL,
            end_label VARCHAR(50) NOT NULL,
            duration_info VARCHAR(100) NOT NULL,
            key_activities JSON NOT NULL,
            role_actions JSON NOT NULL,
            display_order INT NOT NULL DEFAULT 0
        )
    """)
    Database.execute_write("""
        CREATE TABLE IF NOT EXISTS voter_guide_steps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            step_number INT NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            icon VARCHAR(10) NOT NULL DEFAULT '📋',
            documents_required JSON,
            tips JSON,
            role_specific_notes JSON NOT NULL,
            sim_phase_link VARCHAR(30) DEFAULT NULL,
            display_order INT NOT NULL DEFAULT 0
        )
    """)

    # Clear existing data
    Database.execute_write("DELETE FROM election_phases")
    Database.execute_write("DELETE FROM voter_guide_steps")

    # Seed election phases
    print("Seeding election phases...")
    for phase in ELECTION_PHASES:
        Database.execute_write(
            """INSERT INTO election_phases
               (phase_key, title, description, icon, start_label, end_label, duration_info, key_activities, role_actions, display_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                phase['phase_key'], phase['title'], phase['description'],
                phase['icon'], phase['start_label'], phase['end_label'],
                phase['duration_info'],
                json.dumps(phase['key_activities']),
                json.dumps(phase['role_actions']),
                phase['display_order'],
            )
        )
    print(f"   ✅ {len(ELECTION_PHASES)} election phases seeded")

    # Seed voter guide steps
    print("Seeding voter guide steps...")
    for step in VOTER_GUIDE_STEPS:
        Database.execute_write(
            """INSERT INTO voter_guide_steps
               (step_number, title, description, icon, documents_required, tips, role_specific_notes, sim_phase_link, display_order)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                step['step_number'], step['title'], step['description'],
                step['icon'],
                json.dumps(step['documents_required']),
                json.dumps(step['tips']),
                json.dumps(step['role_specific_notes']),
                step.get('sim_phase_link'),
                step['display_order'],
            )
        )
    print(f"   ✅ {len(VOTER_GUIDE_STEPS)} voter guide steps seeded")

    print("\n🗳️  Content seeding complete!")


if __name__ == '__main__':
    seed_content()
