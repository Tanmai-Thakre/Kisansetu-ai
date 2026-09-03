"use client";

// Phase 4 — PriceVsMarket: price comparison badge + advantage display

interface PriceVsMarketProps {
  offeredPrice:   number;
  marketPrice:    number | null;
  priceVsMarket:  string;   // ABOVE_MARKET | AT_MARKET | BELOW_MARKET | UNKNOWN
  priceAdvantage: number | null;
}

export function PriceVsMarketBadge({ priceVsMarket, priceAdvantage, offeredPrice, marketPrice }: PriceVsMarketProps) {
  if (priceVsMarket === "ABOVE_MARKET" && priceAdvantage != null) {
    return (
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-bold text-gray-900">
            ₹{offeredPrice.toLocaleString("en-IN")}
          </span>
          <span className="text-xs font-bold text-white bg-green-500 px-2 py-0.5 rounded-full">
            ↑ +₹{Math.abs(priceAdvantage).toFixed(0)} above market
          </span>
        </div>
        {marketPrice && (
          <p className="text-xs text-gray-400">Market: ₹{marketPrice.toLocaleString("en-IN")}/q</p>
        )}
      </div>
    );
  }

  if (priceVsMarket === "BELOW_MARKET" && priceAdvantage != null) {
    return (
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-bold text-gray-900">
            ₹{offeredPrice.toLocaleString("en-IN")}
          </span>
          <span className="text-xs font-bold text-white bg-red-400 px-2 py-0.5 rounded-full">
            ↓ ₹{Math.abs(priceAdvantage).toFixed(0)} below market
          </span>
        </div>
        {marketPrice && (
          <p className="text-xs text-gray-400">Market: ₹{marketPrice.toLocaleString("en-IN")}/q</p>
        )}
      </div>
    );
  }

  if (priceVsMarket === "AT_MARKET") {
    return (
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-1.5">
          <span className="text-lg font-bold text-gray-900">
            ₹{offeredPrice.toLocaleString("en-IN")}
          </span>
          <span className="text-xs font-bold text-white bg-amber-500 px-2 py-0.5 rounded-full">
            ≈ At market
          </span>
        </div>
        {marketPrice && (
          <p className="text-xs text-gray-400">Market: ₹{marketPrice.toLocaleString("en-IN")}/q</p>
        )}
      </div>
    );
  }

  // Unknown
  return (
    <span className="text-lg font-bold text-gray-900">
      {offeredPrice ? `₹${offeredPrice.toLocaleString("en-IN")}` : "—"}
      <span className="text-xs text-gray-400 font-normal ml-1">/q</span>
    </span>
  );
}
