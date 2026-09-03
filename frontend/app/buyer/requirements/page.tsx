"use client";

import { useLanguage } from "@/hooks/useLanguage";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

export default function BuyerRequirementsPage() {
  const { language, changeLanguage } = useLanguage();
  return (
    <div className="min-h-screen bg-gray-50">
      <Header language={language} onLanguageChange={changeLanguage} farmerName="Gujarat Cotton Traders" role="buyer" />
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        <h1 className="text-xl font-bold text-gray-900">📋 My Requirements</h1>
        <Card>
          <CardContent>
            <p className="text-sm text-amber-700 bg-amber-50 rounded-xl p-3">
              ⚠️ Requirements management coming in Phase 2. Full CRUD for buyer requirements.
            </p>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
