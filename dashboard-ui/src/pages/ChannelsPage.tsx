import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { MessageSquare, CheckCircle, XCircle, Loader2, Globe, Smartphone, Hash, Settings } from 'lucide-react';
import { cn } from '../lib/utils';

const channels = [
  {
    id: 'telegram',
    name: 'Telegram',
    icon: MessageSquare,
    description: 'Telegram bot for messaging',
    color: 'bg-blue-500',
    status: 'connected',
    config: { botToken: '***' },
  },
  {
    id: 'discord',
    name: 'Discord',
    icon: Hash,
    description: 'Discord bot with slash commands',
    color: 'bg-purple-500',
    status: 'disconnected',
    config: { botToken: '' },
  },
  {
    id: 'whatsapp',
    name: 'WhatsApp',
    icon: Smartphone,
    description: 'WhatsApp Business API',
    color: 'bg-green-500',
    status: 'disconnected',
    config: { phoneNumberId: '', accessToken: '' },
  },
];

export function ChannelsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Channels</h1>
          <p className="text-muted-foreground">Configure messaging channel integrations</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {channels.map((channel) => (
          <Card key={channel.id}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={cn('w-12 h-12 rounded-lg flex items-center justify-center', channel.color)}>
                  <channel.icon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle>{channel.name}</CardTitle>
                  <CardDescription>{channel.description}</CardDescription>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span
                  className={cn(
                    'flex items-center gap-1 text-sm px-2 py-1 rounded-full',
                    channel.status === 'connected'
                      ? 'bg-green-500/20 text-green-500'
                      : 'bg-gray-500/20 text-gray-500'
                  )}
                >
                  <span
                    className={cn(
                      'relative h-1.5 w-1.5 rounded-full',
                      channel.status === 'connected' && 'bg-green-500',
                      channel.status === 'disconnected' && 'bg-gray-500'
                    )}
                  />
                  {channel.status === 'connected' ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {channel.id === 'whatsapp' && (
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="Phone Number ID"
                    value={channel.config.phoneNumberId}
                    onChange={(e) => { channel.config.phoneNumberId = e.target.value; }}
                    className="w-full px-3 py-2 text-sm border border-input bg-background rounded-lg"
                  />
                  <input
                    type="password"
                    placeholder="Access Token"
                    value={channel.config.accessToken}
                    onChange={(e) => { channel.config.accessToken = e.target.value; }}
                    className="w-full px-3 py-2 text-sm border border-input bg-background rounded-lg"
                  />
                </div>
              )}
              {channel.id === 'discord' && (
                <div className="space-y-2">
                  <input
                    type="password"
                    placeholder="Bot Token"
                    value={channel.config.botToken}
                    onChange={(e) => { channel.config.botToken = e.target.value; }}
                    className="w-full px-3 py-2 text-sm border border-input bg-background rounded-lg"
                  />
                </div>
              )}
              {channel.id === 'telegram' && (
                <div className="space-y-2">
                  <input
                    type="password"
                    placeholder="Bot Token"
                    value={channel.config.botToken}
                    onChange={(e) => { channel.config.botToken = e.target.value; }}
                    className="w-full px-3 py-2 text-sm border border-input bg-background rounded-lg"
                  />
                </div>
              )}
              <div className="flex gap-2">
                <Button
                  variant={channel.status === 'connected' ? 'secondary' : 'default'}
                  className="flex-1"
                  onClick={() => { channel.status = channel.status === 'connected' ? 'disconnected' : 'connected'; }}
                >
                  {channel.status === 'connected' ? 'Disconnect' : 'Connect'}
                </Button>
                <Button variant="outline" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">
                Webhook URL: <code className="bg-muted px-1 rounded">{window.location.origin}/webhook/{channel.id}</code>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}