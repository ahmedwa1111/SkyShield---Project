import "./globals.css";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

export const metadata = {
  title: "Air Quality App",
  description: "Search and view real-time air quality & weather"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      {/* apply dark theme by default; users can toggle later if needed */}
      <body className="dark flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow container">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
