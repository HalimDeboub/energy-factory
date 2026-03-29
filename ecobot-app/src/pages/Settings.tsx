import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { Button } from "../components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";

export function Settings() {
  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h2 className="text-3xl text-gray-800 mb-2">Settings</h2>
        <p className="text-gray-600">Manage your EcoBot preferences and account settings</p>
      </div>

      {/* Profile Settings */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Profile Settings</CardTitle>
          <CardDescription>Update your personal information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input id="name" placeholder="John Doe" defaultValue="John Doe" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="john@example.com" defaultValue="john@example.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input id="location" placeholder="City, Country" defaultValue="San Francisco, USA" />
          </div>
          <Button className="bg-green-600 hover:bg-green-700">Save Changes</Button>
        </CardContent>
      </Card>

      {/* Energy Settings */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Energy Settings</CardTitle>
          <CardDescription>Configure your energy system details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="solar-capacity">Solar Panel Capacity (kW)</Label>
            <Input id="solar-capacity" type="number" placeholder="5.2" defaultValue="5.2" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="home-size">Home Size (sq ft)</Label>
            <Input id="home-size" type="number" placeholder="2000" defaultValue="2000" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="utility">Utility Provider</Label>
            <Select defaultValue="pge">
              <SelectTrigger id="utility">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pge">PG&E</SelectItem>
                <SelectItem value="sce">Southern California Edison</SelectItem>
                <SelectItem value="sdge">San Diego Gas & Electric</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button className="bg-green-600 hover:bg-green-700">Update Settings</Button>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Manage how you receive updates</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="email-notifs">Email Notifications</Label>
              <p className="text-sm text-gray-500">Receive energy reports via email</p>
            </div>
            <Switch id="email-notifs" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="weekly-report">Weekly Reports</Label>
              <p className="text-sm text-gray-500">Get a weekly summary of your energy usage</p>
            </div>
            <Switch id="weekly-report" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="tips">Energy Saving Tips</Label>
              <p className="text-sm text-gray-500">Receive personalized energy-saving recommendations</p>
            </div>
            <Switch id="tips" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="alerts">High Usage Alerts</Label>
              <p className="text-sm text-gray-500">Get notified when energy usage is above normal</p>
            </div>
            <Switch id="alerts" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
