import time

from app.pipeline import ask

# (no, pertanyaan, seharusnya_dijawab)
PERTANYAAN = [
    (1, "Berapa hari cuti tahunan pegawai tetap?", True),
    (2, "Berapa lama batas waktu pengajuan reimbursement?", True),
    (3, "Jam berapa IT Helpdesk melayani?", True),
    (4, "Berapa hari maksimal WFH dalam seminggu?", True),
    (5, "Berapa nilai maksimal hadiah dari vendor yang boleh diterima?", True),
    (6, "Berapa lama masa probation?", True),
    (7, "Apa saja yang diterima pegawai baru di hari pertama, termasuk akses IT dan hak cuti?", True),
    (8, "Kalau WFH, apa yang wajib dipakai dan biaya internet apa yang bisa diklaim?", True),
    (9, "Apakah pegawai baru yang masih probation boleh WFH dan ambil cuti tahunan?", True),
    (10, "Kalau mau ngajuin cuti harus kapan?", True),
    (11, "Lupa password, harus gimana ya?", True),
    (12, "Berapa gaji pokok seorang manajer?", False),
    (13, "Kapan THR dibayarkan?", False),
    (14, "Siapa CEO perusahaan ini?", False),
    (15, "Bagaimana cara memasak nasi goreng?", False),
]

benar = 0
for no, tanya, harus_dijawab in PERTANYAAN:
    hasil = ask(tanya)
    ok = hasil["grounded"] == harus_dijawab
    benar += ok
    docs = sorted({s["document"] for s in hasil["sources"]})
    print(f"\n#{no} {'PASS' if ok else 'FAIL'} | grounded={hasil['grounded']} | skor={hasil['top_score']}")
    print(f"Q: {tanya}")
    print(f"A: {hasil['answer']}")
    print(f"Sumber: {docs}")
    if hasil["grounded"]:
        time.sleep(4)  # hindari batas request per menit

print(f"\nHASIL: {benar}/{len(PERTANYAAN)} sesuai harapan")