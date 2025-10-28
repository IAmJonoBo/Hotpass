"""Automation helpers for delivering pipeline outputs."""

from .hooks import dispatch_webhooks, push_crm_updates

__all__ = ["dispatch_webhooks", "push_crm_updates"]
