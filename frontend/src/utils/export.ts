import jsPDF from "jspdf";

export function exportRecommendationToCSV(recommendation: any, scenarios: any[] = []) {
  let csv = 'Type,Recommended Coverage,Duration (years)\n';
  csv += `${recommendation.type},${recommendation.recommended_coverage},${recommendation.duration_years}\n`;
  if (scenarios.length > 0) {
    csv += '\nScenario,Recommended Coverage,Type,Duration (years)\n';
    scenarios.forEach((s: any, i: number) => {
      csv += `${["+10% Income", "+1 Dependent", "-50% Existing Coverage"][i]},${s.result.recommended_coverage},${s.result.type},${s.result.duration_years}\n`;
    });
  }
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'life_insurance_recommendation.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export function exportRecommendationToPDF(recommendation: any, scenarios: any[] = []) {
  const doc = new jsPDF();
  doc.setFontSize(16);
  doc.text("Life Insurance Recommendation", 10, 15);
  doc.setFontSize(12);
  doc.text(`Type: ${recommendation.type}`, 10, 30);
  doc.text(`Recommended Coverage: $${recommendation.recommended_coverage.toLocaleString()}`, 10, 40);
  doc.text(`Duration: ${recommendation.duration_years} years`, 10, 50);
  if (scenarios.length > 0) {
    doc.setFontSize(14);
    doc.text("\nScenario Analysis:", 10, 65);
    doc.setFontSize(12);
    scenarios.forEach((s: any, i: number) => {
      doc.text(
        `${["+10% Income", "+1 Dependent", "-50% Existing Coverage"][i]}: $${s.result.recommended_coverage.toLocaleString()} (${s.result.type}, ${s.result.duration_years} years)`,
        10,
        75 + i * 10
      );
    });
  }
  doc.save("life_insurance_recommendation.pdf");
} 