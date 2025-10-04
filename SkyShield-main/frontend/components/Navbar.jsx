"use client";
import React, { useState } from "react";
import { Menu, X } from "lucide-react"; // for mobile menu icons

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className=" top-0 left-0 w-full z-20 text-white">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
        {/* Left: Logo */}
        <div className="font-bold text-xl tracking-widest">
          Sky<br />Shield
        </div>

        {/* Center: Nav links (hidden on mobile) */}
        {/* <ul className="hidden md:flex gap-8 text-sm font-light">
          <li className="cursor-pointer hover:text-gray-300">Technology +</li>
          <li className="cursor-pointer hover:text-gray-300">Mission & Vision</li>
          <li className="cursor-pointer hover:text-gray-300">Satellites +</li>
          <li className="cursor-pointer hover:text-gray-300">Partners</li>
          <li className="cursor-pointer hover:text-gray-300">Careers</li>
          <li className="cursor-pointer hover:text-gray-300">News</li>
        </ul> */}

        {/* Right: Wishlist request */}
        <div className="hidden md:block">
          <a
            href="#A"
            className="text-sm hover:text-gray-300 border-b border-white/40 pb-0.5"
          >
            Dashboard
          </a>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden text-white"
          onClick={() => setOpen(!open)}
        >
          {open ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className="md:hidden bg-black/80 backdrop-blur-lg px-6 py-6 space-y-4">
          <ul className="flex flex-col gap-4 text-sm">
            <li className="cursor-pointer hover:text-gray-300">Technology +</li>
            <li className="cursor-pointer hover:text-gray-300">Mission & Vision</li>
            <li className="cursor-pointer hover:text-gray-300">Satellites +</li>
            <li className="cursor-pointer hover:text-gray-300">Partners</li>
            <li className="cursor-pointer hover:text-gray-300">Careers</li>
            <li className="cursor-pointer hover:text-gray-300">News</li>
          </ul>
          <a
            href="#"
            className="block text-sm hover:text-gray-300 border-b border-white/40 pb-0.5 mt-4"
          >
            Wishlist request
          </a>
        </div>
      )}
    </nav>
  );
}
