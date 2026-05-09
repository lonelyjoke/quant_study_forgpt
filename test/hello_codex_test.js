function summarize(numbers) {
  const total = numbers.reduce((sum, value) => sum + value, 0);
  const average = total / numbers.length;

  return {
    count: numbers.length,
    total,
    average,
    minimum: Math.min(...numbers),
    maximum: Math.max(...numbers),
  };
}

function main() {
  const sample = [3, 7, 11, 18, 23];
  const stats = summarize(sample);

  console.log("Codex code test succeeded.");
  console.log(`Input numbers: ${sample.join(", ")}`);
  console.log(
    `Summary: count=${stats.count}, total=${stats.total}, ` +
      `average=${stats.average.toFixed(2)}, min=${stats.minimum}, max=${stats.maximum}`
  );
}

main();
