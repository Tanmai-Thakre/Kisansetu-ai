"use client";

import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";

export default function AdminDashboardPage() {
  const { language, changeLanguage } = useLanguage();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Admin" role="admin" />
      <main className="max-w-4xl mx-auto px-4 py-6 space-y-5">
        <h1 className="text-xl font-bold text-gray-900">⚙️ Admin Dashboard</h1>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Farmers", value: "5", icon: "🌾" },
            { label: "Total Buyers", value: "3", icon: "🏢" },
            { label: "Market Records", value: "98", icon: "📊" },
            { label: "Active Crops", value: "5", icon: "🌱" },
          ].map(stat => (
            <Card key={stat.label}>
              <CardContent>
                <span className="text-2xl">{stat.icon}</span>
                <p className="text-xl font-bold text-primary-700 mt-2">{stat.value}</p>
                <p className="text-xs text-gray-500">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader><CardTitle>System Status</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { name: "Database", status: "Connected", ok: true },
                { name: "Backend API", status: "Running", ok: true },
                { name: "IBM Granite", status: "Pending Phase 2", ok: false },
                { name: "Real Market API", status: "Pending Phase 2", ok: false },
              ].map(item => (
                <div key={item.name} className="flex justify-between items-center py-2 border-b border-gray-50">
                  <span className="text-sm text-gray-700">{item.name}</span>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${item.ok ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <p className="text-sm text-amber-700 bg-amber-50 rounded-xl p-3">
              ⚠️ All values are DEMO DATA. Full admin panel (user management, market data upload, agent configuration) coming in Phase 2.
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
