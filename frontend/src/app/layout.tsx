import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GapX AI - Skill Gap Intelligence Platform",
  description: "Prepare to become placement and industry ready with personalised roadmaps, coding practice and live AI mock interviews.",
};

// Applies the saved theme before first paint so there's no light/dark flash
const themeScript = `(function(){try{var t=localStorage.getItem('gapx_theme')||'dark';var d=document.documentElement;d.classList.toggle('dark',t==='dark');d.classList.toggle('light',t==='light');}catch(e){}})();`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
