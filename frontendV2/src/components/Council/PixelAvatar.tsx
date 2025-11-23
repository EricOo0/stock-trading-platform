import React from 'react';
import { motion } from 'framer-motion';

interface PixelAvatarProps {
    name: string;
    role: string;
    imageSrc: string;
    isActive: boolean;
    status: 'idle' | 'thinking' | 'speaking';
}

const PixelAvatar: React.FC<PixelAvatarProps> = ({ name, role, imageSrc, isActive, status }) => {
    return (
        <div className="flex flex-col items-center relative group">
            {/* Status Indicator / Speech Bubble Placeholder */}
            {isActive && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute -top-8 bg-white border-2 border-black px-2 py-1 rounded-lg z-10"
                >
                    <p className="text-xs font-bold font-mono text-black">
                        {status === 'thinking' ? 'Thinking...' : 'Speaking!'}
                    </p>
                    {/* Pixel art arrow */}
                    <div className="absolute bottom-[-6px] left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-black"></div>
                </motion.div>
            )}

            {/* Avatar Image */}
            <motion.div
                animate={
                    isActive
                        ? {
                            y: [0, -5, 0],
                            scale: [1, 1.05, 1],
                            filter: "drop-shadow(0 0 8px rgba(255, 255, 0, 0.6))",
                        }
                        : {
                            y: 0,
                            scale: 1,
                            filter: "drop-shadow(0 0 0px rgba(0, 0, 0, 0))",
                        }
                }
                transition={{
                    duration: 1,
                    repeat: isActive ? Infinity : 0,
                    ease: "easeInOut",
                }}
                className={`w-20 h-20 md:w-24 md:h-24 relative ${isActive ? 'z-10' : 'z-0'}`}
            >
                <img
                    src={imageSrc}
                    alt={name}
                    className="w-full h-full object-contain pixelated rendering-pixelated"
                    style={{ imageRendering: 'pixelated' }}
                />
            </motion.div>

            {/* Name Tag */}
            <div className="mt-2 bg-black/80 px-2 py-1 rounded border border-white/20 backdrop-blur-sm">
                <p className={`text-xs font-mono text-center ${isActive ? 'text-yellow-400 font-bold' : 'text-gray-300'}`}>
                    {name}
                </p>
                <p className="text-[10px] text-gray-500 text-center uppercase tracking-wider">{role}</p>
            </div>
        </div>
    );
};

export default PixelAvatar;
