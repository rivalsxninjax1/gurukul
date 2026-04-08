from database.connection import get_session
from models.expense import Expense
from utils.bs_converter import bs_month_ad_range, today_bs_tuple, prev_bs_month
from datetime import date
import logging

logger = logging.getLogger(__name__)


def add_expense(title: str, amount: float,
                expense_date: date, description: str = "") -> int:
    session = get_session()
    e = Expense(
        title       = title,
        amount      = amount,
        date        = expense_date,
        description = description,
    )
    session.add(e)
    session.commit()
    eid = e.id
    session.close()
    logger.info(f"Expense {eid}: {title} Rs.{amount}")
    return eid


def get_all_expenses() -> list:
    session = get_session()
    rows = session.query(Expense).order_by(Expense.date.desc()).all()
    result = [{
        "id":          e.id,
        "title":       e.title,
        "amount":      e.amount,
        "date":        e.date,
        "description": e.description or "",
    } for e in rows]
    session.close()
    return result


def delete_expense(expense_id: int):
    session = get_session()
    e = session.query(Expense).get(expense_id)
    if e:
        session.delete(e)
        session.commit()
    session.close()


def get_expense_dashboard_stats() -> dict:
    """
    Returns:
      total_all_time  : sum of all expenses
      current_bs_month: sum of expenses in current BS month
      previous_bs_month: sum of expenses in previous BS month
    """
    session = get_session()
    all_exp = session.query(Expense).all()

    total_all = sum(e.amount for e in all_exp)

    # Current BS month range
    by, bm, _ = today_bs_tuple()
    cur_start, cur_end = bs_month_ad_range(by, bm)
    cur_total = sum(
        e.amount for e in all_exp
        if cur_start and cur_end and cur_start <= e.date <= cur_end
    )

    # Previous BS month
    py, pm = prev_bs_month(by, bm)
    prev_start, prev_end = bs_month_ad_range(py, pm)
    prev_total = sum(
        e.amount for e in all_exp
        if prev_start and prev_end and prev_start <= e.date <= prev_end
    )

    session.close()
    return {
        "total_all_time":    total_all,
        "current_bs_month":  cur_total,
        "previous_bs_month": prev_total,
    }


def get_total_revenue() -> float:
    """Total paid amount across ALL subscriptions (including deleted students)."""
    from models.subscription import SubscriptionPayment
    session = get_session()
    total = sum(p.amount_paid for p in session.query(SubscriptionPayment).all())
    session.close()
    return total


def get_net_balance() -> float:
    """Net = total collected revenue - total expenses."""
    return get_total_revenue() - get_expense_dashboard_stats()["total_all_time"]