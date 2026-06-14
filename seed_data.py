import os
import sys
import datetime
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.club import Club, ClubMembership, ClubMemberRole, ClubApplication, ClubApplicationStatus
from app.models.event import Event, EventRSVP, RSVPStatus, EventType
from app.models.announcement import Announcement
from app.utils.security import hash_password

def seed_data():
    db = SessionLocal()

    try:
        print("Seeding Users...")
        users_data = [
            ("alice@campus.edu",   "Alice Smith",      "student",        "password"),
            ("bob@campus.edu",     "Bob Johnson",      "student",        "password"),
            ("charlie@campus.edu", "Charlie Brown",    "student",        "password"),
            ("dave@campus.edu",    "Dave Wilson",      "student",        "password"),
            ("eve@campus.edu",     "Eve Davis",        "student",        "password"),
            ("frank@campus.edu",   "Frank Miller",     "student",        "password"),
            ("grace@campus.edu",   "Grace Lee",        "student",        "password"),
            ("henry@campus.edu",   "Henry Adams",      "student",        "password"),
            ("ivy@campus.edu",     "Ivy Chen",         "student",        "password"),
            ("jack@campus.edu",    "Jack Taylor",      "student",        "password"),
            ("faculty@campus.edu", "Dr. Priya Sharma", "faculty_advisor","password"),
            ("dr.james@campus.edu","Dr. James Roy",    "faculty_advisor","password"),
        ]

        seeded_users = []
        for email, name, role, pwd in users_data:
            user = db.query(User).filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    full_name=name,
                    role=getattr(UserRole, role),
                    password_hash=hash_password(pwd),
                    is_active=True,
                )
                db.add(user)
                db.flush()
                print(f"  Created user: {name}")
            else:
                print(f"  Skipping existing user: {name}")
            seeded_users.append(user)

        students = [u for u in seeded_users if u.role == UserRole.student]
        faculty  = [u for u in seeded_users if u.role == UserRole.faculty_advisor]

        print("\nSeeding Clubs...")
        clubs_data = [
            {
                "name":        "Tech Innovators Club",
                "description": "A hub for tech enthusiasts to build, hack, and innovate. We run workshops, hackathons, and open-source sprints every semester.",
                "domain":      "Technology",
                "president":   students[0],
                "advisor":     faculty[0],
                "members":     students[1:5],
                "join_type":   "open",
            },
            {
                "name":        "Photography Society",
                "description": "Capture the world through your lens. From DSLR basics to advanced post-processing, we cover it all with weekly photo walks and competitions.",
                "domain":      "Arts",
                "president":   students[1],
                "advisor":     faculty[0],
                "members":     students[2:6],
                "join_type":   "open",
            },
            {
                "name":        "Robotics Club",
                "description": "Building autonomous robots, competing in national competitions, and exploring the frontier of embedded systems and AI-powered machines.",
                "domain":      "Engineering",
                "president":   students[2],
                "advisor":     faculty[1],
                "members":     students[3:7],
                "join_type":   "open",
            },
            {
                "name":        "Design Studio",
                "description": "Where pixels meet purpose. We work on UI/UX, graphic design, branding, and motion graphics. Open to all creative minds on campus.",
                "domain":      "Design",
                "president":   students[3],
                "advisor":     faculty[1],
                "members":     students[4:8],
                "join_type":   "open",
            },
            {
                "name":        "Hiking & Adventure Club",
                "description": "Explore the great outdoors! Monthly treks, survival skill workshops, and an annual expedition for adventurers at all skill levels.",
                "domain":      "Sports",
                "president":   students[4],
                "advisor":     faculty[0],
                "members":     students[5:9],
                "join_type":   "open",
            },
            {
                "name":        "Debate & MUN Society",
                "description": "Sharpen your critical thinking and public speaking. We participate in Model UN conferences and host our own inter-college debate tournaments.",
                "domain":      "Academia",
                "president":   students[5],
                "advisor":     faculty[1],
                "members":     students[6:10],
                "join_type":   "invite_only",
            },
        ]

        seeded_clubs = []
        for c in clubs_data:
            club = db.query(Club).filter_by(name=c["name"]).first()
            if not club:
                from app.models.club import JoinType
                club = Club(
                    name=c["name"],
                    description=c["description"],
                    domain=c["domain"],
                    faculty_advisor_id=c["advisor"].id,
                    logo_url=f"https://api.dicebear.com/7.x/initials/svg?seed={c['name'].replace(' ', '+')}",
                    join_type=getattr(JoinType, c["join_type"]),
                )
                db.add(club)
                db.flush()
                # President
                db.add(ClubMembership(club_id=club.id, user_id=c["president"].id, role=ClubMemberRole.president))
                # Members
                for m in c["members"]:
                    db.add(ClubMembership(club_id=club.id, user_id=m.id, role=ClubMemberRole.member))
                db.flush()
                print(f"  Created club: {c['name']}")
            else:
                print(f"  Skipping existing club: {c['name']}")
            seeded_clubs.append(club)

        print("\nSeeding Events...")
        now = datetime.datetime.utcnow()
        events_data = [
            # Tech Innovators
            dict(club=seeded_clubs[0], title="AI & ML Hackathon", description="A 24-hour hackathon where teams build AI-powered applications. Cash prizes for top 3 teams!", venue="Main Auditorium", start=now+datetime.timedelta(days=7), seats=120, approved=True, tags=["AI","ML","hackathon"]),
            dict(club=seeded_clubs[0], title="Intro to Python Workshop", description="A beginner-friendly Python workshop covering syntax, data structures, and building a simple project.", venue="Lab 201", start=now+datetime.timedelta(days=2), seats=50, approved=True, tags=["python","beginner","workshop"]),
            dict(club=seeded_clubs[0], title="Open Source Sprint", description="Contribute to real open-source projects with guidance from seniors. Pick an issue, submit a PR!", venue="CS Building, Room 305", start=now+datetime.timedelta(days=14), seats=40, approved=True, tags=["open-source","coding"]),
            dict(club=seeded_clubs[0], title="Cloud Computing Seminar", description="Introduction to AWS, GCP, and Azure. Hands-on labs included.", venue="Seminar Hall 2", start=now+datetime.timedelta(days=21), seats=80, approved=False, tags=["cloud","AWS","seminar"]),

            # Photography
            dict(club=seeded_clubs[1], title="Campus Photo Walk", description="Join us for a guided photo walk around campus. All skill levels and camera types welcome.", venue="Campus Grounds", start=now+datetime.timedelta(days=3), seats=20, approved=True, tags=["photography","outdoor"]),
            dict(club=seeded_clubs[1], title="Lightroom Editing Workshop", description="Learn to edit RAW photos like a pro using Adobe Lightroom. Bring your laptop!", venue="Media Lab, Block C", start=now+datetime.timedelta(days=10), seats=30, approved=True, tags=["lightroom","editing","workshop"]),
            dict(club=seeded_clubs[1], title="Portrait Photography Masterclass", description="Guest photographer from National Geographic shares techniques for stunning portraits.", venue="Studio 1, Arts Building", start=now+datetime.timedelta(days=18), seats=15, approved=False, tags=["portrait","masterclass"]),

            # Robotics
            dict(club=seeded_clubs[2], title="Sumo Bot Competition", description="Watch student-built robots battle it out in the ring! Open to spectators. Teams can register separately.", venue="Engineering Block Courtyard", start=now+datetime.timedelta(days=14), seats=200, approved=True, tags=["robotics","competition"]),
            dict(club=seeded_clubs[2], title="Intro to Arduino", description="Build your first embedded system with Arduino. All components provided. No prior experience needed.", venue="Lab 104, Electronics Dept.", start=now+datetime.timedelta(days=4), seats=35, approved=True, tags=["arduino","embedded","beginner"]),
            dict(club=seeded_clubs[2], title="ROS2 Workshop", description="Introduction to the Robot Operating System 2. Simulate robots and write your first ROS node.", venue="Robotics Lab", start=now+datetime.timedelta(days=25), seats=25, approved=True, tags=["ROS","robotics","workshop"]),

            # Design Studio
            dict(club=seeded_clubs[3], title="Figma UI/UX Workshop", description="Hands-on introduction to Figma. Design a mobile app screen from scratch, with feedback from industry designers.", venue="Design Room, Block D", start=now+datetime.timedelta(days=5), seats=40, approved=True, tags=["figma","UI/UX","design"]),
            dict(club=seeded_clubs[3], title="Brand Identity Design Sprint", description="48-hour sprint to create a complete brand identity (logo, colors, typography) for a fictional startup.", venue="Design Room, Block D", start=now+datetime.timedelta(days=12), seats=30, approved=True, tags=["branding","sprint","design"]),

            # Hiking
            dict(club=seeded_clubs[4], title="Weekend Forest Trek", description="A 12km trek through the nearby forest reserve. Moderate difficulty. Includes breakfast and a campfire!", venue="Meetup at Main Gate", start=now+datetime.timedelta(days=1), seats=25, approved=True, tags=["trekking","outdoor","nature"]),
            dict(club=seeded_clubs[4], title="Survival Skills Workshop", description="Learn fire-starting, navigation, first aid, and shelter-building in an outdoor setting.", venue="College Grounds, Behind Sports Complex", start=now+datetime.timedelta(days=9), seats=30, approved=True, tags=["survival","outdoor","workshop"]),

            # Debate & MUN
            dict(club=seeded_clubs[5], title="Intra-College Debate Championship", description="Annual debate competition. Topics span politics, technology, and ethics. All students may watch; registered teams compete.", venue="Main Auditorium", start=now+datetime.timedelta(days=20), seats=300, approved=True, tags=["debate","competition"]),
            dict(club=seeded_clubs[5], title="MUN Conference Prep", description="Prep sessions for the upcoming inter-college Model United Nations conference. Committee assignment, position paper writing, and practice rounds.", venue="Conference Room A", start=now+datetime.timedelta(days=8), seats=50, approved=True, tags=["MUN","debate","preparation"]),
        ]

        seeded_events = []
        for ev in events_data:
            event = db.query(Event).filter_by(title=ev["title"]).first()
            if not event:
                event = Event(
                    club_id=ev["club"].id,
                    title=ev["title"],
                    description=ev["description"],
                    venue=ev["venue"],
                    start_at=ev["start"],
                    end_at=ev["start"] + datetime.timedelta(hours=3),
                    seat_limit=ev["seats"],
                    is_approved=ev["approved"],
                    is_cancelled=False,
                    is_hidden=False,
                    tags=ev.get("tags", []),
                    event_type=EventType.open,
                    qr_token=f"qr_{ev['title'].lower().replace(' ', '_')}_{random.randint(1000,9999)}",
                )
                db.add(event)
                db.flush()
                # Add RSVPs from random students
                rsvp_users = random.sample(students, min(5, len(students)))
                for u in rsvp_users:
                    db.add(EventRSVP(event_id=event.id, user_id=u.id, status=RSVPStatus.confirmed))
                print(f"  Created event: {ev['title']}")
            else:
                print(f"  Skipping existing event: {ev['title']}")
            seeded_events.append(event)

        print("\nSeeding Announcements...")
        # Each announcement is authored by that club's president
        announcements_data = [
            (seeded_clubs[0], clubs_data[0]["president"], "New Semester, New Projects!", "We're kicking off this semester with exciting project ideas. Join our Discord to vote on what we build next!"),
            (seeded_clubs[1], clubs_data[1]["president"], "Photo Competition Results", "Congratulations to Ivy Chen for winning Best Landscape in our Annual Photo Competition!"),
            (seeded_clubs[2], clubs_data[2]["president"], "Team Selection for Nationals", "Tryouts for the National Robotics Championship are open. Email robotics@campus.edu with your portfolio."),
            (seeded_clubs[3], clubs_data[3]["president"], "Design Resources Available", "Check our shared Google Drive for free Figma templates, icon packs, and font collections to use in your projects."),
            (seeded_clubs[4], clubs_data[4]["president"], "Trek Rescheduled", "Due to weather forecasts, the Monsoon Trek has been moved to next weekend. All existing registrations are valid."),
            (seeded_clubs[5], clubs_data[5]["president"], "New MUN Committee Assignments", "Assignments for the upcoming inter-college MUN are out. Check your email for your committee and country."),
        ]

        for club, author, title, body in announcements_data:
            existing = db.query(Announcement).filter_by(title=title).first()
            if not existing:
                db.add(Announcement(club_id=club.id, author_id=author.id, title=title, body=body))
                print(f"  Created announcement: {title}")

        print("\nSeeding Club Applications...")
        apps_data = [
            (students[6], "Astronomy Club", "We want to bring stargazing, telescope sessions, and astrophotography to campus!", "science"),
            (students[7], "Chess Club", "Competitive and casual chess for all skill levels, with weekly tournaments.", "games"),
            (students[8], "Green Campus Initiative", "A sustainability club focused on campus eco-drives, tree planting, and reducing waste.", "environment"),
        ]
        for applicant, club_name, desc, domain in apps_data:
            existing = db.query(ClubApplication).filter_by(club_name=club_name).first()
            if not existing:
                db.add(ClubApplication(
                    applicant_id=applicant.id,
                    club_name=club_name,
                    description=desc,
                    domain=domain,
                    status=ClubApplicationStatus.pending,
                ))
                print(f"  Created club application: {club_name}")

        db.commit()
        print("\n[OK] Database seeded successfully!")
        print(f"   Users: {len(users_data)}")
        print(f"   Clubs: {len(clubs_data)}")
        print(f"   Events: {len(events_data)}")
        print(f"   Announcements: {len(announcements_data)}")
        print(f"   Club Applications: {len(apps_data)}")

    except Exception as e:
        db.rollback()
        import traceback
        print(f"\n[ERROR] Error seeding data: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
