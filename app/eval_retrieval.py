from app.retriever import retrieve

# (no, pertanyaan, kategori, dokumen sumber yang diharapkan)
PERTANYAAN = [
    (1, "Berapa hari cuti tahunan pegawai tetap?", "ADA", "kebijakan_cuti.md"),
    (2, "Berapa lama batas waktu pengajuan reimbursement?", "ADA", "prosedur_reimbursement.md"),
    (3, "Jam berapa IT Helpdesk melayani?", "ADA", "sop_it_helpdesk.md"),
    (4, "Berapa hari maksimal WFH dalam seminggu?", "ADA", "kebijakan_wfh.md"),
    (5, "Berapa nilai maksimal hadiah dari vendor yang boleh diterima?", "ADA", "kode_etik.md"),
    (6, "Berapa lama masa probation?", "ADA", "panduan_onboarding.md"),
    (7, "Apa saja yang diterima pegawai baru di hari pertama, termasuk akses IT dan hak cuti?", "LINTAS", "panduan_onboarding.md"),
    (8, "Kalau WFH, apa yang wajib dipakai dan biaya internet apa yang bisa diklaim?", "LINTAS", "kebijakan_wfh.md"),
    (9, "Apakah pegawai baru yang masih probation boleh WFH dan ambil cuti tahunan?", "LINTAS", "panduan_onboarding.md"),
    (10, "Kalau mau ngajuin cuti harus kapan?", "INFORMAL", "kebijakan_cuti.md"),
    (11, "Lupa password, harus gimana ya?", "INFORMAL", "sop_it_helpdesk.md"),
    (12, "Berapa gaji pokok seorang manajer?", "TIDAK ADA", "-"),
    (13, "Kapan THR dibayarkan?", "TIDAK ADA", "-"),
    (14, "Siapa CEO perusahaan ini?", "TIDAK ADA", "-"),
    (15, "Bagaimana cara memasak nasi goreng?", "TIDAK ADA", "-"),
]

for no, tanya, kategori, harapan in PERTANYAAN:
    hits = retrieve(tanya, top_k=3)
    print(f"\n#{no} [{kategori}] {tanya}")
    print(f"   diharapkan: {harapan}")
    for h in hits:
        print(f"   {h['score']:.3f} | {h['source']} | {h['section']}")