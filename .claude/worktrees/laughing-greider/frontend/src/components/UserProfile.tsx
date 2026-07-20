import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  User, 
  Mail, 
  Calendar, 
  Shield, 
  Camera, 
  Save, 
  Loader2, 
  Eye, 
  EyeOff,
  AlertTriangle,
  LogOut
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { authService } from "@/services/authService";
import { useToast } from "@/hooks/use-toast";

const UserProfile = () => {
  const { user, logout, updateProfile } = useAuth();
  const { toast } = useToast();

  // Profile form states
  const [profileData, setProfileData] = useState({
    firstName: user?.firstName || "",
    lastName: user?.lastName || "",
    email: user?.email || "",
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileErrors, setProfileErrors] = useState<{ [key: string]: string }>({});

  // Password change states
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState<{ [key: string]: string }>({});

  // Logout confirmation dialog
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);

  if (!user) {
    return null;
  }

  const getUserInitials = () => {
    const firstInitial = user.firstName?.charAt(0) || user.email?.charAt(0) || "";
    const lastInitial = user.lastName?.charAt(0) || "";
    return `${firstInitial}${lastInitial}`.toUpperCase();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // Profile update handlers
  const handleProfileInputChange = (field: keyof typeof profileData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setProfileData(prev => ({ ...prev, [field]: e.target.value }));
    if (profileErrors[field]) {
      setProfileErrors(prev => ({ ...prev, [field]: "" }));
    }
  };

  const validateProfileForm = () => {
    const errors: { [key: string]: string } = {};

    if (!profileData.firstName.trim()) {
      errors.firstName = "First name is required";
    }
    if (!profileData.lastName.trim()) {
      errors.lastName = "Last name is required";
    }
    if (!profileData.email.trim()) {
      errors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(profileData.email)) {
      errors.email = "Please enter a valid email address";
    }

    setProfileErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateProfileForm()) return;

    setProfileLoading(true);
    try {
      await updateProfile({
        firstName: profileData.firstName.trim(),
        lastName: profileData.lastName.trim(),
        email: profileData.email.trim(),
      });

      toast({
        title: "Profile updated",
        description: "Your profile information has been successfully updated.",
      });
    } catch (error: any) {
      const errorMessage = error.message || "Failed to update profile";
      setProfileErrors({ general: errorMessage });
      toast({
        title: "Update failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setProfileLoading(false);
    }
  };

  // Password change handlers
  const handlePasswordInputChange = (field: keyof typeof passwordData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setPasswordData(prev => ({ ...prev, [field]: e.target.value }));
    if (passwordErrors[field]) {
      setPasswordErrors(prev => ({ ...prev, [field]: "" }));
    }
  };

  const validatePasswordForm = () => {
    const errors: { [key: string]: string } = {};

    if (!passwordData.currentPassword) {
      errors.currentPassword = "Current password is required";
    }
    if (!passwordData.newPassword) {
      errors.newPassword = "New password is required";
    } else if (passwordData.newPassword.length < 8) {
      errors.newPassword = "Password must be at least 8 characters";
    }
    if (!passwordData.confirmPassword) {
      errors.confirmPassword = "Please confirm your new password";
    } else if (passwordData.newPassword !== passwordData.confirmPassword) {
      errors.confirmPassword = "Passwords do not match";
    }

    setPasswordErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validatePasswordForm()) return;

    setPasswordLoading(true);
    try {
      await authService.changePassword({
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword,
      });

      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });

      toast({
        title: "Password updated",
        description: "Your password has been successfully changed.",
      });
    } catch (error: any) {
      const errorMessage = error.message || "Failed to change password";
      setPasswordErrors({ general: errorMessage });
      toast({
        title: "Password change failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    toast({
      title: "Signed out",
      description: "You have been successfully signed out.",
    });
  };

  return (
    <div id="user-profile" className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Profile Header */}
      <Card id="profile-header-card" className="glass border-white/10">
        <CardContent id="profile-header-content" className="pt-6">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="relative">
              <Avatar id="profile-avatar" className="w-24 h-24">
                <AvatarImage src={user.profileImage} alt={`${user.firstName} ${user.lastName}`} />
                <AvatarFallback className="text-xl bg-gradient-to-br from-primary to-success text-white">
                  {getUserInitials()}
                </AvatarFallback>
              </Avatar>
              <Button
                id="change-avatar-button"
                size="sm"
                className="absolute -bottom-2 -right-2 rounded-full w-8 h-8 p-0"
                variant="secondary"
              >
                <Camera className="w-4 h-4" />
              </Button>
            </div>
            <div className="text-center sm:text-left space-y-2">
              <h1 className="text-2xl font-bold">
                {user.firstName} {user.lastName}
              </h1>
              <div className="flex flex-col sm:flex-row gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4" />
                  {user.email}
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Member since {formatDate(user.createdAt)}
                </div>
              </div>
            </div>
            <div className="ml-auto">
              <Dialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
                <DialogTrigger asChild>
                  <Button id="logout-button" variant="outline" className="glass border-white/20">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </Button>
                </DialogTrigger>
                <DialogContent id="logout-dialog">
                  <DialogHeader>
                    <DialogTitle>Sign Out</DialogTitle>
                    <DialogDescription>
                      Are you sure you want to sign out of your account?
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button
                      id="logout-cancel-button"
                      variant="outline"
                      onClick={() => setShowLogoutDialog(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      id="logout-confirm-button"
                      variant="destructive"
                      onClick={handleLogout}
                    >
                      Sign Out
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Profile Settings Tabs */}
      <Tabs id="profile-tabs" defaultValue="profile" className="space-y-6">
        <TabsList id="profile-tabs-list" className="grid w-full grid-cols-2 glass border-white/10">
          <TabsTrigger id="profile-tab" value="profile">
            <User className="w-4 h-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger id="security-tab" value="security">
            <Shield className="w-4 h-4 mr-2" />
            Security
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent id="profile-tab-content" value="profile">
          <Card id="profile-form-card" className="glass border-white/10">
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and contact details.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleProfileSubmit}>
              <CardContent id="profile-form-content" className="space-y-4">
                {profileErrors.general && (
                  <Alert id="profile-error-alert" variant="destructive">
                    <AlertDescription>{profileErrors.general}</AlertDescription>
                  </Alert>
                )}

                <div id="name-fields" className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      type="text"
                      value={profileData.firstName}
                      onChange={handleProfileInputChange("firstName")}
                      className={`glass border-white/20 ${profileErrors.firstName ? 'border-destructive' : ''}`}
                      disabled={profileLoading}
                    />
                    {profileErrors.firstName && (
                      <p id="firstName-error" className="text-sm text-destructive">{profileErrors.firstName}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      type="text"
                      value={profileData.lastName}
                      onChange={handleProfileInputChange("lastName")}
                      className={`glass border-white/20 ${profileErrors.lastName ? 'border-destructive' : ''}`}
                      disabled={profileLoading}
                    />
                    {profileErrors.lastName && (
                      <p id="lastName-error" className="text-sm text-destructive">{profileErrors.lastName}</p>
                    )}
                  </div>
                </div>

                <div id="email-field" className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={profileData.email}
                    onChange={handleProfileInputChange("email")}
                    className={`glass border-white/20 ${profileErrors.email ? 'border-destructive' : ''}`}
                    disabled={profileLoading}
                  />
                  {profileErrors.email && (
                    <p id="email-error" className="text-sm text-destructive">{profileErrors.email}</p>
                  )}
                </div>

                <div className="flex justify-end pt-4">
                  <Button
                    id="save-profile-button"
                    type="submit"
                    className="bg-gradient-to-r from-primary to-primary-hover hover:shadow-glow"
                    disabled={profileLoading}
                  >
                    {profileLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </form>
          </Card>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent id="security-tab-content" value="security">
          <Card id="password-form-card" className="glass border-white/10">
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>
                Update your password to keep your account secure.
              </CardDescription>
            </CardHeader>
            <form onSubmit={handlePasswordSubmit}>
              <CardContent id="password-form-content" className="space-y-4">
                {passwordErrors.general && (
                  <Alert id="password-error-alert" variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{passwordErrors.general}</AlertDescription>
                  </Alert>
                )}

                <div id="current-password-field" className="space-y-2">
                  <Label htmlFor="currentPassword">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="currentPassword"
                      type={showPasswords.current ? "text" : "password"}
                      value={passwordData.currentPassword}
                      onChange={handlePasswordInputChange("currentPassword")}
                      className={`glass border-white/20 pr-10 ${passwordErrors.currentPassword ? 'border-destructive' : ''}`}
                      disabled={passwordLoading}
                    />
                    <Button
                      id="toggle-current-password"
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPasswords(prev => ({ ...prev, current: !prev.current }))}
                    >
                      {showPasswords.current ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                  {passwordErrors.currentPassword && (
                    <p id="current-password-error" className="text-sm text-destructive">{passwordErrors.currentPassword}</p>
                  )}
                </div>

                <div id="new-password-field" className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <div className="relative">
                    <Input
                      id="newPassword"
                      type={showPasswords.new ? "text" : "password"}
                      value={passwordData.newPassword}
                      onChange={handlePasswordInputChange("newPassword")}
                      className={`glass border-white/20 pr-10 ${passwordErrors.newPassword ? 'border-destructive' : ''}`}
                      disabled={passwordLoading}
                    />
                    <Button
                      id="toggle-new-password"
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPasswords(prev => ({ ...prev, new: !prev.new }))}
                    >
                      {showPasswords.new ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                  {passwordErrors.newPassword && (
                    <p id="new-password-error" className="text-sm text-destructive">{passwordErrors.newPassword}</p>
                  )}
                </div>

                <div id="confirm-new-password-field" className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showPasswords.confirm ? "text" : "password"}
                      value={passwordData.confirmPassword}
                      onChange={handlePasswordInputChange("confirmPassword")}
                      className={`glass border-white/20 pr-10 ${passwordErrors.confirmPassword ? 'border-destructive' : ''}`}
                      disabled={passwordLoading}
                    />
                    <Button
                      id="toggle-confirm-password"
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPasswords(prev => ({ ...prev, confirm: !prev.confirm }))}
                    >
                      {showPasswords.confirm ? (
                        <EyeOff className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Eye className="h-4 w-4 text-muted-foreground" />
                      )}
                    </Button>
                  </div>
                  {passwordErrors.confirmPassword && (
                    <p id="confirm-password-error" className="text-sm text-destructive">{passwordErrors.confirmPassword}</p>
                  )}
                </div>

                <div className="flex justify-end pt-4">
                  <Button
                    id="change-password-button"
                    type="submit"
                    className="bg-gradient-to-r from-primary to-primary-hover hover:shadow-glow"
                    disabled={passwordLoading}
                  >
                    {passwordLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Updating...
                      </>
                    ) : (
                      <>
                        <Shield className="mr-2 h-4 w-4" />
                        Update Password
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </form>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default UserProfile;