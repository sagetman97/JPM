import Papa from "papaparse";
import * as XLSX from "xlsx";

export function parseClientCSV(file: File): Promise<Record<string, any>> {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      complete: (results: Papa.ParseResult<any>) => {
        if (results.data && results.data.length > 0) {
          const row = results.data[0];
          resolve({
            age: row.age || "",
            income: row.income || "",
            dependents: row.dependents || "",
            existingCoverage: row.existingCoverage || "",
          });
        } else {
          reject(new Error("No data found in file"));
        }
      },
      error: (err: any) => reject(err),
    });
  });
}

export function parseClientXLSX(file: File): Promise<Record<string, any>> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: "array" });
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 }) as any[][];
      if (rows.length < 2) return reject(new Error("No data found in file"));
      const headers = rows[0].map((h: any) => String(h).toLowerCase());
      const values = rows[1];
      const row: Record<string, any> = {};
      headers.forEach((h, i) => {
        row[h] = values[i];
      });
      resolve({
        age: row.age || "",
        income: row.income || "",
        dependents: row.dependents || "",
        existingCoverage: row.existingCoverage || "",
      });
    };
    reader.onerror = (err) => reject(err);
    reader.readAsArrayBuffer(file);
  });
} 