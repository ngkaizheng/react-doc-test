import { useState } from 'react'
import './App.css'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import {
  Dialog,
  DialogTrigger,
  DialogContent,
} from '@/components/ui/dialog'
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui/tabs'
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectGroup,
  SelectItem,
} from '@/components/ui/select'
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu'
import { Toaster, toast } from 'sonner'
import { StatusCard } from './components/shared-ui'

const stats = [
  { label: 'Active Users', value: '2,847', change: '+12%', variant: 'default' as const },
  { label: 'Revenue', value: '$48,290', change: '+8%', variant: 'secondary' as const },
  { label: 'Bounce Rate', value: '24.1%', change: '-3%', variant: 'destructive' as const },
  { label: 'Load Time', value: '142ms', change: '-18%', variant: 'outline' as const },
]

const recentActivity = [
  { id: 1, user: 'Alice Chen', action: 'Deployed v2.4.1', time: '2m ago', badge: 'success' as const },
  { id: 2, user: 'Bob Martinez', action: 'Updated config.yml', time: '15m ago', badge: 'warning' as const },
  { id: 3, user: 'Carol Wu', action: 'Failed backup job', time: '1h ago', badge: 'error' as const },
  { id: 4, user: 'Dave Kim', action: 'Added API key', time: '2h ago', badge: 'success' as const },
]

function App() {
  const [count, setCount] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTab, setSelectedTab] = useState('overview')

  const handleSimulateLoad = () => {
    setIsLoading(true)
    setTimeout(() => {
      setIsLoading(false)
      toast.success('Data refreshed successfully!')
    }, 2000)
  }

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-zinc-100 p-6 space-y-6">
        {/* Header */}
        <header className="flex items-center justify-between max-w-6xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold text-zinc-900">Dashboard</h1>
            <p className="text-sm text-zinc-500">Welcome back, here's what's happening.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleSimulateLoad} disabled={isLoading}>
              {isLoading ? <Spinner className="size-4" /> : null}
              {isLoading ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Dialog>
              <DialogTrigger render={<Button>Add Widget</Button>} />
              <DialogContent>
                <h2 className="text-lg font-semibold">New Widget</h2>
                <p className="text-sm text-zinc-500">This is a demo dialog. Add your form here.</p>
                <div className="flex justify-end gap-2 mt-4">
                  <Button variant="outline">Cancel</Button>
                  <Button>Create</Button>
                </div>
              </DialogContent>
            </Dialog>
            <DropdownMenu>
              <DropdownMenuTrigger render={<Button variant="ghost" className="size-8 rounded-full bg-zinc-200" />}>
                <span className="text-xs font-bold">JD</span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuGroup>
                  <DropdownMenuItem>Profile</DropdownMenuItem>
                  <DropdownMenuItem>Settings</DropdownMenuItem>
                  <DropdownMenuItem>Log out</DropdownMenuItem>
                </DropdownMenuGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-6xl mx-auto">
          {stats.map((stat) => (
            <Card key={stat.label} size="sm">
              <CardHeader>
                <CardDescription>{stat.label}</CardDescription>
                <CardTitle className="text-2xl">{stat.value}</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant={stat.variant}>{stat.change}</Badge>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto">
          <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v)}>
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
              <TabsTrigger value="status">System Status</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Overview</CardTitle>
                  <CardDescription>
                    Select a time range and explore key metrics.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Select defaultValue="7d">
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectItem value="24h">Last 24 hours</SelectItem>
                          <SelectItem value="7d">Last 7 days</SelectItem>
                          <SelectItem value="30d">Last 30 days</SelectItem>
                          <SelectItem value="90d">Last 90 days</SelectItem>
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                    <Button variant="outline" size="sm">Export</Button>
                    <Button size="sm">Generate Report</Button>
                  </div>

                  <div className="rounded-lg border border-dashed border-zinc-300 p-12 text-center text-zinc-400 text-sm">
                    Chart area — integrate your favorite chart library here
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="activity" className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>Latest actions across the platform.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {recentActivity.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-zinc-50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="size-8 rounded-full bg-zinc-200 flex items-center justify-center text-xs font-medium text-zinc-600">
                          {item.user.split(' ').map(n => n[0]).join('')}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-zinc-800">{item.user}</p>
                          <p className="text-xs text-zinc-500">{item.action}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={item.badge === 'error' ? 'destructive' : item.badge === 'warning' ? 'outline' : 'default'}
                        >
                          {item.badge}
                        </Badge>
                        <span className="text-xs text-zinc-400">{item.time}</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
                <CardFooter>
                  <Button variant="ghost" className="w-full">View all activity</Button>
                </CardFooter>
              </Card>
            </TabsContent>

            <TabsContent value="status" className="mt-4 space-y-4">
              <StatusCard
                status="success"
                title="All Systems Operational"
              />
              <StatusCard
                status="warning"
                title="Database Replication Lag"
                isHighlighted
              />
              <StatusCard
                status="error"
                title="Backup Service Failure"
                onRetry={() => toast.info('Retrying backup service...')}
                isHighlighted
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Counter footer */}
        <footer className="text-center text-xs text-zinc-400 max-w-6xl mx-auto">
          <Button variant="link" size="xs" onClick={() => setCount((c) => c + 1)}>
            Clicks: {count}
          </Button>
        </footer>
      </div>

      <Toaster position="bottom-right" />
    </>
  )
}

export default App
