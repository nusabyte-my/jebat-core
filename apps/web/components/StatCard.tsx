"use client";
import { motion } from "framer-motion";

interface StatCardProps {
  value: string;
  label: string;
  icon: string;
  delay?: number;
}

export function StatCard({ value, label, icon, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ scale: 1.05, borderColor: "rgba(34,211,238,0.3)" }}
      className="rounded-2xl border border-white/5 bg-white/[0.02] p-4 cursor-default"
    >
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">{value}</div>
      <div className="text-xs text-neutral-500">{label}</div>
    </motion.div>
  );
}
