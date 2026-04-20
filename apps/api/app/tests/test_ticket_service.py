"""Tests for ticket_service (state-machine + lifecycle helpers)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.services import ticket_service


async def _seed_company(db: AsyncSession) -> str:
    company = Company(
        id=uuid.uuid4(),
        slug=f"tc-{uuid.uuid4().hex[:8]}",
        name="Ticket Test Co",
    )
    db.add(company)
    await db.commit()
    return str(company.id)


class TestValidateTicketTransition:
    def test_draft_to_triage_allowed(self):
        assert ticket_service.validate_ticket_transition("draft", "triage") is True

    def test_triage_to_done_not_allowed(self):
        assert ticket_service.validate_ticket_transition("triage", "done") is False

    def test_terminal_cancelled_can_only_reopen(self):
        allowed = ticket_service.TICKET_TRANSITIONS["cancelled"]
        assert allowed == ["reopened"]

    def test_unknown_source_status_returns_false(self):
        assert ticket_service.validate_ticket_transition("bogus", "done") is False


@pytest.mark.asyncio
async def test_create_ticket_starts_in_draft_and_numbers_incrementally(
    db_session: AsyncSession,
):
    company_id = await _seed_company(db_session)
    first = await ticket_service.create_ticket(db=db_session, company_id=company_id, title="First")
    second = await ticket_service.create_ticket(
        db=db_session, company_id=company_id, title="Second"
    )
    assert first.status == "draft"
    assert first.ticket_no == 1
    assert second.ticket_no == 2


@pytest.mark.asyncio
async def test_transition_ticket_advances_state(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    ticket = await ticket_service.create_ticket(
        db=db_session, company_id=company_id, title="Lifecycle"
    )
    triaged = await ticket_service.transition_ticket(
        db=db_session, ticket=ticket, new_status="triage"
    )
    assert triaged.status == "triage"
    planning = await ticket_service.transition_ticket(
        db=db_session, ticket=triaged, new_status="planning"
    )
    assert planning.status == "planning"


@pytest.mark.asyncio
async def test_transition_ticket_rejects_invalid_jump(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    ticket = await ticket_service.create_ticket(
        db=db_session, company_id=company_id, title="Bad path"
    )
    with pytest.raises(ValueError):
        await ticket_service.transition_ticket(db=db_session, ticket=ticket, new_status="done")


@pytest.mark.asyncio
async def test_add_thread_message_persists(db_session: AsyncSession):
    company_id = await _seed_company(db_session)
    ticket = await ticket_service.create_ticket(
        db=db_session, company_id=company_id, title="With thread"
    )
    msg = await ticket_service.add_thread_message(
        db=db_session,
        ticket=ticket,
        body_markdown="hello",
        author_type="system",
    )
    assert msg.id is not None
    assert msg.body_markdown == "hello"
    assert msg.author_type == "system"
    assert str(msg.ticket_id) == str(ticket.id)
