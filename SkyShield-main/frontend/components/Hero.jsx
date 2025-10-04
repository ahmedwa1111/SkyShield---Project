'use client';
import React from "react";
import { motion } from "framer-motion";

export default function Hero() {
  return (
    <section className="relative w-screen h-screen overflow-hidden text-white">
      {/* Background Video */}
      <video
        autoPlay
        muted
        loop
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover"
      >
        <source src="/earth.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Overlay */}
      <div className="absolute inset-0 bg-black/50"></div>

      {/* Content */}
      <div className="relative z-10 py-26 flex flex-col justify-end h-full px-8 md:px-20 max-w-4xl">
        <motion.h1
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 1 }}
          className="text-4xl md:text-6xl font-bold leading-tight"
        >
Clean Air, Clear Future        </motion.h1>

        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 1 }}
          className="mt-4 text-lg md:text-xl text-gray-300 max-w-2xl"
        >
          We harness NASA’s Earth data and real-time weather insights to deliver accurate forecasts, empower healthier choices, and protect people from the risks of air pollution.
        </motion.p>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 1 }}
          className="mt-8"
        >
          <button className="px-6 py-3 bg-white text-black font-semibold rounded-xl shadow-lg hover:bg-gray-200 transition">
            Check Air Quality
          </button>
        </motion.div>
      </div>

      

      {/* Small Moon Icon Bottom Right */}
      <div className="absolute bottom-6 right-6 z-10">
        <img src="/moon.png" alt="Moon" className="w-16 h-16" />
      </div>
    </section>
  );
}
