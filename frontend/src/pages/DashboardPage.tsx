import { Navigation } from "@/components/Navigation";
import { Dashboard } from "@/components/Dashboard";
import { ParticleBackground } from "@/components/ParticleBackground";

const DashboardPage = () => {
  return (
    <div className="relative min-h-screen">
      <ParticleBackground />
      <Navigation />
      <Dashboard />
    </div>
  );
};

export default DashboardPage;