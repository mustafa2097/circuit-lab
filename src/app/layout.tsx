import type { Metadata } from "next";
import { IBM_Plex_Sans_Arabic } from "next/font/google";
import "./globals.css";

const arabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-arabic",
});

export const metadata: Metadata = {
  title: "مختبر دوائر PLC",
  description: "محاكي تركيب وتشغيل دوائر الريليه وPLC مطابق للملزمة",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl">
      <body className={`${arabic.variable} font-sans antialiased`}>
        <div className="min-h-screen bg-white text-gray-900">{children}</div>
      </body>
    </html>
  );
}
