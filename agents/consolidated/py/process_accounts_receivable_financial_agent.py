"""
ProcessAccountsReceivableFinancialAgent - APQC 8.0 Agent
8.2.2 Process Accounts Receivable
APQC Blueprint ID: apqc_8_0_d5e6f7g8
Version: 1.0.0
"""

import os
import psutil
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin


@dataclass
class ProcessAccountsReceivableFinancialAgentConfig:
    apqc_agent_id: str = "apqc_8_0_d5e6f7g8"
    apqc_process_id: str = "8.2.2"
    agent_name: str = "process_accounts_receivable_financial_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"
    autonomous_level: float = 0.9
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class ProcessAccountsReceivableFinancialAgent(BaseAgent, ProtocolMixin):
    """
    Skills: aging_analysis: 0.9, dso_calculation: 0.88, payment_prediction: 0.85
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "8.2.2"

    def __init__(self, config: ProcessAccountsReceivableFinancialAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {"aging_analysis": 0.9, "dso_calculation": 0.88, "payment_prediction": 0.85}
        self.state = {"status": "initialized", "tasks_processed": 0}

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = await self._process_accounts_receivable(input_data)
            self.state["tasks_processed"] += 1
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _process_accounts_receivable(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process AR with aging analysis and DSO calculation

        Business Logic:
        1. Calculate AR aging buckets (0-30, 31-60, 61-90, 90+ days)
        2. Calculate Days Sales Outstanding (DSO)
        3. Predict payment probability
        4. Prioritize collections
        """
        invoices = input_data.get("invoices", [])
        payments = input_data.get("payments", [])
        customer_history = input_data.get("customer_payment_history", {})
        current_date = datetime.fromisoformat(
            input_data.get("current_date", datetime.now().isoformat())
        )

        # AR Aging Analysis
        aging_analysis = self._calculate_ar_aging(invoices, current_date)

        # DSO Calculation
        dso = self._calculate_dso(invoices, payments, current_date)

        # Payment Prediction
        payment_predictions = self._predict_payments(invoices, customer_history, current_date)

        # Collection Priorities
        collection_priorities = self._prioritize_collections(aging_analysis, payment_predictions)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "ar_analysis": {
                    "aging_report": aging_analysis,
                    "dso": dso,
                    "total_outstanding": aging_analysis["total_outstanding"],
                    "overdue_amount": aging_analysis["overdue_amount"],
                },
                "payment_predictions": payment_predictions,
                "collection_priorities": collection_priorities,
                "metrics": {
                    "dso_days": dso["dso_days"],
                    "collection_effectiveness": dso["collection_effectiveness"],
                    "at_risk_amount": collection_priorities["high_risk_amount"],
                },
            },
        }

    def _calculate_ar_aging(self, invoices: List[Dict], current_date: datetime) -> Dict[str, Any]:
        """Calculate AR aging buckets"""
        aging_buckets = {
            "current_0_30": [],
            "past_due_31_60": [],
            "past_due_61_90": [],
            "past_due_over_90": [],
        }

        totals = {
            "current_0_30": 0,
            "past_due_31_60": 0,
            "past_due_61_90": 0,
            "past_due_over_90": 0,
        }

        for invoice in invoices:
            invoice_date = datetime.fromisoformat(
                invoice.get("invoice_date", current_date.isoformat())
            )
            due_date = datetime.fromisoformat(invoice.get("due_date", current_date.isoformat()))
            amount = invoice.get("amount", 0)
            paid_amount = invoice.get("paid_amount", 0)
            outstanding = amount - paid_amount

            if outstanding <= 0:
                continue

            days_outstanding = (current_date - invoice_date).days
            days_overdue = (current_date - due_date).days

            invoice_info = {
                "invoice_id": invoice.get("invoice_id"),
                "customer": invoice.get("customer_name"),
                "amount": outstanding,
                "days_outstanding": days_outstanding,
                "days_overdue": max(0, days_overdue),
            }

            if days_overdue < 0:  # Not yet due
                aging_buckets["current_0_30"].append(invoice_info)
                totals["current_0_30"] += outstanding
            elif days_overdue <= 30:
                aging_buckets["current_0_30"].append(invoice_info)
                totals["current_0_30"] += outstanding
            elif days_overdue <= 60:
                aging_buckets["past_due_31_60"].append(invoice_info)
                totals["past_due_31_60"] += outstanding
            elif days_overdue <= 90:
                aging_buckets["past_due_61_90"].append(invoice_info)
                totals["past_due_61_90"] += outstanding
            else:
                aging_buckets["past_due_over_90"].append(invoice_info)
                totals["past_due_over_90"] += outstanding

        total_outstanding = sum(totals.values())
        overdue_amount = (
            totals["past_due_31_60"] + totals["past_due_61_90"] + totals["past_due_over_90"]
        )

        return {
            "aging_buckets": {
                k: {"count": len(v), "total": round(totals[k], 2), "invoices": v[:5]}  # Top 5
                for k, v in aging_buckets.items()
            },
            "total_outstanding": round(total_outstanding, 2),
            "overdue_amount": round(overdue_amount, 2),
            "overdue_percentage": (
                round((overdue_amount / total_outstanding * 100), 2) if total_outstanding > 0 else 0
            ),
        }

    def _calculate_dso(
        self, invoices: List[Dict], payments: List[Dict], current_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate Days Sales Outstanding (DSO)
        DSO = (Accounts Receivable / Total Credit Sales) * Number of Days
        """
        # Calculate AR
        total_ar = sum(inv.get("amount", 0) - inv.get("paid_amount", 0) for inv in invoices)

        # Calculate total credit sales for last 90 days
        ninety_days_ago = current_date - timedelta(days=90)
        recent_sales = []

        for invoice in invoices:
            inv_date = datetime.fromisoformat(invoice.get("invoice_date", current_date.isoformat()))
            if inv_date >= ninety_days_ago:
                recent_sales.append(invoice.get("amount", 0))

        total_credit_sales = sum(recent_sales)
        average_daily_sales = total_credit_sales / 90 if total_credit_sales > 0 else 1

        # Calculate DSO
        dso_days = total_ar / average_daily_sales if average_daily_sales > 0 else 0

        # Calculate collection effectiveness index
        total_collected = sum(p.get("amount", 0) for p in payments)
        collection_effectiveness = (
            (total_collected / (total_collected + total_ar) * 100)
            if (total_collected + total_ar) > 0
            else 0
        )

        return {
            "dso_days": round(dso_days, 1),
            "total_ar": round(total_ar, 2),
            "average_daily_sales": round(average_daily_sales, 2),
            "collection_effectiveness": round(collection_effectiveness, 2),
            "status": (
                "excellent"
                if dso_days < 30
                else "good" if dso_days < 45 else "needs_improvement" if dso_days < 60 else "poor"
            ),
        }

    def _predict_payments(
        self, invoices: List[Dict], customer_history: Dict, current_date: datetime
    ) -> Dict[str, Any]:
        """
        Predict payment probability based on customer history
        """
        predictions = []

        for invoice in invoices:
            amount = invoice.get("amount", 0)
            paid_amount = invoice.get("paid_amount", 0)
            outstanding = amount - paid_amount

            if outstanding <= 0:
                continue

            customer = invoice.get("customer_name", "Unknown")
            customer_hist = customer_history.get(customer, {})

            # Calculate payment probability based on history
            on_time_payments = customer_hist.get("on_time_payments", 0)
            late_payments = customer_hist.get("late_payments", 0)
            total_payments = on_time_payments + late_payments

            if total_payments > 0:
                on_time_rate = on_time_payments / total_payments
                payment_probability = on_time_rate * 100
            else:
                payment_probability = 50  # Default for new customers

            # Adjust based on amount
            if outstanding > customer_hist.get("average_invoice", 0) * 2:
                payment_probability *= 0.9  # Reduce probability for unusually large invoices

            due_date = datetime.fromisoformat(invoice.get("due_date", current_date.isoformat()))
            days_until_due = (due_date - current_date).days

            predictions.append(
                {
                    "invoice_id": invoice.get("invoice_id"),
                    "customer": customer,
                    "outstanding": round(outstanding, 2),
                    "payment_probability": round(payment_probability, 1),
                    "days_until_due": days_until_due,
                    "risk_level": (
                        "low"
                        if payment_probability > 75
                        else "medium" if payment_probability > 50 else "high"
                    ),
                }
            )

        # Sort by risk
        predictions.sort(key=lambda x: x["payment_probability"])

        return {
            "predictions": predictions,
            "high_risk_count": len([p for p in predictions if p["risk_level"] == "high"]),
            "medium_risk_count": len([p for p in predictions if p["risk_level"] == "medium"]),
            "low_risk_count": len([p for p in predictions if p["risk_level"] == "low"]),
        }

    def _prioritize_collections(self, aging: Dict, predictions: Dict) -> Dict[str, Any]:
        """
        Prioritize collections based on aging and payment predictions
        """
        priorities = []

        # High priority: Over 90 days or high risk
        for pred in predictions["predictions"]:
            if pred["risk_level"] == "high" or pred["days_until_due"] < -90:
                priorities.append(
                    {
                        "invoice_id": pred["invoice_id"],
                        "customer": pred["customer"],
                        "amount": pred["outstanding"],
                        "priority": "high",
                        "reason": "High risk or significantly overdue",
                        "recommended_action": "Immediate contact and escalation",
                    }
                )

        # Medium priority: 60-90 days or medium risk
        for pred in predictions["predictions"]:
            if pred["risk_level"] == "medium" and -90 < pred["days_until_due"] < -60:
                priorities.append(
                    {
                        "invoice_id": pred["invoice_id"],
                        "customer": pred["customer"],
                        "amount": pred["outstanding"],
                        "priority": "medium",
                        "reason": "Moderate risk and overdue",
                        "recommended_action": "Follow-up communication",
                    }
                )

        high_risk_amount = sum(p["amount"] for p in priorities if p["priority"] == "high")

        return {
            "collection_priorities": priorities[:10],  # Top 10
            "high_priority_count": len([p for p in priorities if p["priority"] == "high"]),
            "medium_priority_count": len([p for p in priorities if p["priority"] == "medium"]),
            "high_risk_amount": round(high_risk_amount, 2),
        }

    def log(self, level: str, message: str):
        print(f"[{datetime.now().isoformat()}] [{level.upper()}] {message}")


def create_process_accounts_receivable_financial_agent(
    config: Optional[ProcessAccountsReceivableFinancialAgentConfig] = None,
):
    if config is None:
        config = ProcessAccountsReceivableFinancialAgentConfig()
    return ProcessAccountsReceivableFinancialAgent(config)
