import "./globals.css";

export const metadata = {
  title: "DIP Studio",
  description: "Digital Image Processing pipeline",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
