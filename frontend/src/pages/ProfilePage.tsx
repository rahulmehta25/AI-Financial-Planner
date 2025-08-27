import { Navigation } from "@/components/Navigation";
import UserProfile from "@/components/UserProfile";

const ProfilePage = () => {
  return (
    <div id="profile-page" className="min-h-screen bg-gradient-to-br from-background via-background to-muted">
      <Navigation />
      <div className="pt-20 pb-8">
        <UserProfile />
      </div>
    </div>
  );
};

export default ProfilePage;