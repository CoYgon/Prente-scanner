// nmap-komutlari.ts
export interface NmapKomut {
  komutAdi: string;
  parametre: string; // Nmap'e verilen komut kısmı (örn: '-sS -A -T4')
  aciklama: string; // Komutun yaptığı işin kısa özeti
  kullanimAmaci: 'Keşif' | 'Port Tarama' | 'OS/Servis Tespiti' | 'IDS/Güvenlik Duvarı Aşma' | 'Script Taraması';
  ornekKullanim: string; // Hedef IP'siz örnek (örn: 'nmap -sS -A')
  riskSeviyesi: 'Düşük' | 'Orta' | 'Yüksek'; // Hedefe karşı ne kadar "gürültülü" olduğu
}