"use client";

import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { BottomNav, SideNav } from "@/components/layout/Navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

export default function ProfilePage() {
  const { language, t, changeLanguage } = useLanguage();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Rameshbhai Patel" role="farmer" />
      <div className="flex">
        <SideNav />
        <main className="flex-1 max-w-2xl mx-auto px-4 py-6 pb-28 sm:pb-8 space-y-5">
          <h1 className="text-xl font-bold text-gray-900">👤 {t("profile.title")}</h1>

          {/* Avatar card */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 text-center">
            <div className="w-20 h-20 bg-primary-600 rounded-full flex items-center justify-center text-white text-3xl font-bold mx-auto">R</div>
            <p className="text-xl font-bold text-gray-900 mt-3">Rameshbhai Patel</p>
            <p className="text-sm text-gray-500">🌾 Farmer • Rajkot, Gujarat</p>
            <Badge variant="green" className="mt-2">Active</Badge>
          </div>

          <Card>
            <CardHeader><CardTitle>Farm Details</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { label: t("profile.village"), value: "Gondal" },
                  { label: t("profile.district"), value: "Rajkot" },
                  { label: t("profile.state"), value: "Gujarat" },
                  { label: t("profile.land_area"), value: "12.5 acres" },
                ].map(item => (
                  <div key={item.label} className="flex justify-between py-2 border-b border-gray-50">
                    <span className="text-sm text-gray-500">{item.label}</span>
                    <span className="text-sm font-medium text-gray-900">{item.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>My Crops</CardTitle></CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  { crop: "🌿 Cotton (Bt Cotton)", qty: "150 qtl", grade: "Grade A", status: "Ready to sell" },
                ].map(c => (
                  <div key={c.crop} className="bg-green-50 rounded-xl p-3 border border-green-100">
                    <div className="flex justify-between items-start">
                      <p className="font-medium text-gray-900">{c.crop}</p>
                      <Badge variant="green">{c.grade}</Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{c.qty} • {c.status}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-amber-600 mt-3">⚠️ DEMO DATA</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Language</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-2">
                {(["en", "gu", "hi"] as const).map(lang => (
                  <button
                    key={lang}
                    onClick={() => changeLanguage(lang)}
                    className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-colors ${
                      language === lang
                        ? "bg-primary-600 text-white border-primary-600"
                        : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                    }`}
                  >
                    {lang === "en" ? "English" : lang === "gu" ? "ગુજરાતી" : "हिन्दी"}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Button variant="outline" size="lg" fullWidth>
            🚪 Logout
          </Button>
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
