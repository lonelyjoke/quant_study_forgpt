function dailyReturns(prices) {
  return prices.slice(1).map((price, index) => price / prices[index] - 1);
}

function summarizeReturns(returns) {
  const total = returns.reduce((sum, value) => sum + value, 0);

  return {
    days: returns.length,
    averageReturn: total / returns.length,
    bestDay: Math.max(...returns),
    worstDay: Math.min(...returns),
  };
}

function main() {
  const prices = [100.0, 101.5, 100.8, 103.2, 102.9];
  const returns = dailyReturns(prices);
  const summary = summarizeReturns(returns);

  console.log("Codex smoke test succeeded.");
  console.log(`Prices: ${prices.join(", ")}`);
  console.log(
    `Daily returns: ${returns.map((value) => `${(value * 100).toFixed(2)}%`).join(", ")}`
  );
  console.log(
    `Summary: days=${summary.days}, avg=${(summary.averageReturn * 100).toFixed(2)}%, ` +
      `best=${(summary.bestDay * 100).toFixed(2)}%, worst=${(summary.worstDay * 100).toFixed(2)}%`
  );
}

main();
