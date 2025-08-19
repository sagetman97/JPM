export function generateShareableLink(form: any, result: any, scenarios: any[]) {
  const params = new URLSearchParams();
  params.set("age", form.age);
  params.set("income", form.income);
  params.set("dependents", form.dependents);
  params.set("existingCoverage", form.existingCoverage);
  if (result) {
    params.set("rec", btoa(JSON.stringify(result)));
  }
  if (scenarios && scenarios.length > 0) {
    params.set("scenarios", btoa(JSON.stringify(scenarios)));
  }
  return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
}

export function parseShareableLink(search: string) {
  const params = new URLSearchParams(search);
  const form = {
    age: params.get("age") || "",
    income: params.get("income") || "",
    dependents: params.get("dependents") || "",
    existingCoverage: params.get("existingCoverage") || "",
  };
  let result = null;
  let scenarios: any[] = [];
  if (params.get("rec")) {
    try { result = JSON.parse(atob(params.get("rec")!)); } catch {}
  }
  if (params.get("scenarios")) {
    try { scenarios = JSON.parse(atob(params.get("scenarios")!)); } catch {}
  }
  return { form, result, scenarios };
} 