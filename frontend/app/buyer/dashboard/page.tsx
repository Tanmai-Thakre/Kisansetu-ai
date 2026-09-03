"use client";

// Phase 4 — /buyer/dashboard: Shows incoming farmer requests + stats.

import { useEffect, useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import api, { endpoints } from "@/lib/api";
import type { ConnectionRequest } from "@/types";

// Demo buyer id (no auth yet in Phase 4)
const DEMO_BUYER_ID = 1;

const STATUS_CONFIG = {
  PENDING:   { label: "Pending",   color: "bg-amber-100 text-amber-700"  },
  ACCEPTED:  { label: "Accepted",  color: "bg-green-100 text-green-700"  },
  REJECTED:  { label: "Rejected",  color: "bg-red-100 text-red-700"      },
  COMPLETED: { label: "Completed", color: "bg-blue-100 text-blue-700"    },
} as const;

export default function BuyerDashboardPage() {
  const { language, changeLanguage } = useLanguage();

  const [requests,  setRequests]  = useState<ConnectionRequest[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [updating,  setUpdating]  = useState<number | null>(null);
  const [error,     setError]     = useState("");

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const res = await api.get(endpoints.buyerRequests, {
        params: { buyer_id: DEMO_BUYER_ID },
      });
      setRequests(res.data as ConnectionRequest[]);
    } catch {
      setError("Could not load requests. Start the backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRequests(); }, []);

  const updateStatus = async (id: number, status: string) => {
    setUpdating(id);
    try {
      await api.patch(`${endpoints.buyerRequests}/${id}`, { status });
      setRequests(prev =>
        prev.map(r => r.id === id ? { ...r, status: status as ConnectionRequest["status"] } : r)
      );
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg || "Failed to update request status.");
    } finally {
      setUpdating(null);
    }
  };

  const pending  = requests.filter(r => r.status === "PENDING");
  const accepted = requests.filter(r => r.status === "ACCEPTED");

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage}
        farmerName="Gujarat Cotton Traders" role="buyer" />
      <main className="max-w-2xl mx-auto px-4 py-6 pb-10 space-y-5">

        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">🏢 Buyer Dashboard</h1>
          <Badge variant="purple">Phase 4 Active</Badge>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Pending",   value: pending.length,             icon: "⏳", color: "text-amber-600" },
            { label: "Accepted",  value: accepted.length,            icon: "✅", color: "text-green-600" },
            { label: "Total",     value: requests.length,            icon: "📋", color: "text-blue-600"  },
            { label: "Completed", value: requests.filter(r => r.status === "COMPLETED").length, icon: "🏁", color: "text-gray-600" },
          ].map(stat => (
            <Card key={stat.label}>
              <CardContent>
                <span className="text-2xl">{stat.icon}</span>
                <p className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-sm text-amber-700">
            ⚠️ {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="space-y-3 animate-pulse">
            {[1, 2].map(i => <div key={i} className="h-28 bg-gray-100 rounded-2xl" />)}
          </div>
        )}

        {/* Incoming requests */}
        {!loading && (
          <>
            <div className="flex items-center justify-between">
              <h2 className="font-bold text-gray-800">Incoming Farmer Requests</h2>
              <button onClick={fetchRequests} className="text-xs text-indigo-600 font-medium hover:underline">
                🔄 Refresh
              </button>
            </div>

            {requests.length === 0 ? (
              <Card>
                <CardContent>
                  <div className="text-center py-8">
                    <p className="text-3xl mb-2">📭</p>
                    <p className="font-semibold text-gray-600">No requests yet</p>
                    <p className="text-xs text-gray-400 mt-1">
                      Farmer requests will appear here once farmers send connection requests.
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {requests.map(req => {
                  const cfg = STATUS_CONFIG[req.status] ?? STATUS_CONFIG.PENDING;
                  const isPending = req.status === "PENDING";
                  const isAccepted = req.status === "ACCEPTED";
                  const busy = updating === req.id;
                  return (
                    <Card key={req.id}>
                      <CardContent>
                        <div className="flex items-start justify-between gap-3 mb-3">
                          <div>
                            <p className="font-semibold text-gray-900">
                              {req.crop === "cotton" ? "🌿" : "🥜"}{" "}
                              {req.crop.charAt(0).toUpperCase() + req.crop.slice(1)} — {req.quantity} qtl
                            </p>
                            <p className="text-xs text-gray-500 mt-0.5">
                              Farmer #{req.farmer_id}
                              {req.offered_price ? ` · ₹${req.offered_price.toLocaleString("en-IN")}/q` : ""}
                              {req.match_score ? ` · ${req.match_score.toFixed(0)}/100 match` : ""}
                            </p>
                            {req.message && (
                              <p className="text-xs text-gray-400 mt-1 italic">"{req.message}"</p>
                            )}
                          </div>
                          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.color}`}>
                            {cfg.label}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 mb-3">
                          Submitted {new Date(req.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                        </p>

                        {/* Action buttons */}
                        {isPending && (
                          <div className="flex gap-2">
                            <Button variant="primary" size="sm" fullWidth
                              disabled={busy}
                              onClick={() => updateStatus(req.id, "ACCEPTED")}>
                              {busy ? "…" : "✓ Accept"}
                            </Button>
                            <Button variant="outline" size="sm" fullWidth
                              disabled={busy}
                              onClick={() => updateStatus(req.id, "REJECTED")}>
                              {busy ? "…" : "✗ Reject"}
                            </Button>
                          </div>
                        )}
                        {isAccepted && (
                          <Button variant="outline" size="sm" fullWidth
                            disabled={busy}
                            onClick={() => updateStatus(req.id, "COMPLETED")}>
                            {busy ? "…" : "🏁 Mark Completed"}
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </>
        )}

        <div className="text-xs text-amber-700 bg-amber-50 rounded-2xl p-3 border border-amber-200">
          ⚠️ <strong>DEMO DATA</strong> — Buyer ID {DEMO_BUYER_ID} shown. Full auth coming in Phase 5.
        </div>
      </main>
    </div>
  );
}
