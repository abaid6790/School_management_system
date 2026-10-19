import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"   # platform-level, no school_id, oversees all schools
    ADMIN = "admin"               # school-level admin, created at school registration
    TEACHER = "teacher"
    ACCOUNTANT = "accountant"
    RECEPTIONIST = "receptionist"
    PARENT = "parent"             # added in a later phase
    STUDENT = "student"           # added in a later phase


class SubjectType(str, enum.Enum):
    CORE = "core"
    ELECTIVE = "elective"
    PRACTICAL = "practical"
    THEORY = "theory"


class RecordStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class StudentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    GRADUATED = "graduated"
    TRANSFERRED = "transferred"
    WITHDRAWN = "withdrawn"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    PROMOTED = "promoted"
    REPEATED = "repeated"
    TRANSFERRED = "transferred"
    WITHDRAWN = "withdrawn"
    GRADUATED = "graduated"


class GuardianRelation(str, enum.Enum):
    FATHER = "father"
    MOTHER = "mother"
    GUARDIAN = "guardian"
    OTHER = "other"


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    RESIGNED = "resigned"
    TERMINATED = "terminated"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"
    LEAVE = "leave"


class ApplicantRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    STAFF = "staff"


class LeaveType(str, enum.Enum):
    SICK = "sick"
    CASUAL = "casual"
    ANNUAL = "annual"
    EMERGENCY = "emergency"
    OTHER = "other"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ExamType(str, enum.Enum):
    MIDTERM = "midterm"
    FINAL = "final"
    MONTHLY_TEST = "monthly_test"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    PRACTICAL = "practical"
    CUSTOM = "custom"


class ExamStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CHEQUE = "cheque"
    MOBILE_WALLET = "mobile_wallet"
    OTHER = "other"


class DiscountType(str, enum.Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    SCHOLARSHIP = "scholarship"
    NEED_BASED = "need_based"
    CUSTOM = "custom"


class FeeStatus(str, enum.Enum):
    """Never stored — always computed from amount/discounts/payments/due_date.
    Defined here only so templates and filter dropdowns share one literal set."""
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    UNPAID = "unpaid"
    OVERDUE = "overdue"


class SalaryRecipientRole(str, enum.Enum):
    TEACHER = "teacher"
    STAFF = "staff"


class SalaryPaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class DocumentType(str, enum.Enum):
    ADMISSION_FORM = "admission_form"
    BIRTH_CERTIFICATE = "birth_certificate"
    PREVIOUS_SCHOOL_CERTIFICATE = "previous_school_certificate"
    CNIC_BFORM = "cnic_bform"
    TRANSFER_CERTIFICATE = "transfer_certificate"
    OTHER = "other"
