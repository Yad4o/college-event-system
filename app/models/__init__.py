# Import all models here so that SQLAlchemy metadata (and Alembic) can see every table.
# Order follows FK dependencies: users -> clubs -> events -> everything else.

from app.models.user import User, UserRole  # noqa: F401
from app.models.club import Club, ClubMembership, ClubApplication, JoinType, ClubMemberRole, ClubApplicationStatus  # noqa: F401
from app.models.event import Event, EventRSVP, EventAttendance, EventPhoto, EventFeedback, EventType, RSVPStatus  # noqa: F401
from app.models.announcement import Announcement  # noqa: F401
from app.models.certificate import Certificate, Badge, UserBadge, CertificateType  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
from app.models.recruitment import RecruitmentDrive, RecruitmentApplication, RecruitmentApplicationStatus  # noqa: F401
from app.models.budget import Budget, BudgetItem, Sponsor, BudgetItemCategory  # noqa: F401
