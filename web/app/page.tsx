
export default async function Page() {
  const res = await fetch('http://localhost:3001/api/countries', { cache: 'no-store' });
  const countries = await res.json();
  return (
    <main style={{fontFamily:'system-ui', padding: 24}}>
      <h1>Trust Index — Starter</h1>
      <p>Connected to API: listing countries (seeded)</p>
      <ul>
        {countries.map((c:any) => <li key={c.iso3}>{c.name} ({c.iso3})</li>)}
      </ul>
      <p>Next steps: wire Map component and call /api/score & /api/country/[iso3].</p>
    </main>
  );
}
