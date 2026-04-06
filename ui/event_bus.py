from PyQt5.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    attendance_imported    = pyqtSignal()
    payment_added          = pyqtSignal()
    student_saved          = pyqtSignal()
    billing_updated        = pyqtSignal()
    open_student_profile   = pyqtSignal(int)
    open_teacher_profile   = pyqtSignal(int)


bus = EventBus()