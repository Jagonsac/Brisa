export function getSafetyColor(score) {
  if (score >= 80) return '#1a9850';
  if (score >= 65) return '#66bd63';
  if (score >= 50) return '#fee08b';
  if (score >= 35) return '#f46d43';
  return '#d73027';
}
