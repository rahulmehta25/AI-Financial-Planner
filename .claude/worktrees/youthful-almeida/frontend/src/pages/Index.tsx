import { Navigation } from "@/components/Navigation";
import { HeroSection } from "@/components/HeroSection";
import { ParticleBackground } from "@/components/ParticleBackground";

const Index = () => {
  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <Navigation />
      <HeroSection />
    </div>
  );
};

export default Index;
