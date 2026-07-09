import React from 'react';
import { Calendar, Save, BookOpen, Tag, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn, formatRelativeTime } from '@/lib/utils';
import { api } from '@/lib/api';
import { useAuth } from '@/lib/auth-provider';

interface JournalEntry {
  id: string;
  date: string;
  content: string;
  mood: 'great' | 'good' | 'neutral' | 'bad' | 'terrible';
  tags: string[];
  created_at: string;
  updated_at: string;
}

export function JournalPage() {
  const { user } = useAuth();
  const [selectedDate, setSelectedDate] = React.useState(() => new Date().toISOString().split('T')[0]);
  const [entry, setEntry] = React.useState(null);
  const [content, setContent] = React.useState('');
  const [mood, setMood] = React.useState('neutral');
  const [tags, setTags] = React.useState([]);
  const [tagInput, setTagInput] = React.useState('');
  const [entries, setEntries] = React.useState([]);
  const [saving, setSaving] = React.useState(false);
  const [viewMode, setViewMode] = React.useState('edit');
  const [calendarDate, setCalendarDate] = React.useState(new Date());

  const formatDateKey = (date: Date) => date.toISOString().split('T')[0];
  const parseDate = (dateStr: string) => new Date(dateStr + 'T00:00:00');

  React.useEffect(() => {
    const stored = localStorage.getItem('jebat_journal');
    if (stored) {
      try {
        setEntries(JSON.parse(stored));
      } catch {
        setEntries([]);
      }
    }
    loadEntryForDate(selectedDate);
  }, []);

  const loadEntryForDate = (date: string) => {
    const found = entries.find(e => e.date === date);
    if (found) {
      setEntry(found);
      setContent(found.content);
      setMood(found.mood);
      setTags(found.tags);
    } else {
      setEntry(null);
      setContent('');
      setMood('neutral');
      setTags([]);
    }
  };

  const saveEntry = async () => {
    if (!content.trim() && tags.length === 0) return;
    
    setSaving(true);
    const now = new Date().toISOString();
    const updated: any = {
      id: entry?.id || crypto.randomUUID(),
      date: selectedDate,
      content,
      mood,
      tags,
      created_at: entry?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    const updatedEntries = entries.filter(e => e.date !== selectedDate);
    updatedEntries.push(updated);
    localStorage.setItem('jebat_journal', JSON.stringify(updatedEntries));
    setEntries(updatedEntries);
    setEntry(updated);
    setSaving(false);
  };

  const addTag = () => {
    const tag = tagInput.trim().toLowerCase();
    if (tag && !tags.includes(tag) && /^[a-z0-9_-]+$/.test(tag)) {
      setTags([...tags, tag]);
      setTagInput('');
    }
  };

  const handleTagKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') { e.preventDefault(); addTag(); }
    if (e.key === ' ' && tagInput.endsWith('#')) { e.preventDefault(); addTag(); }
  };

  const deleteEntry = () => {
    if (confirm('Delete this journal entry?')) {
      const updatedEntries = entries.filter(e => e.date !== selectedDate);
      localStorage.setItem('jebat_journal', JSON.stringify(updatedEntries));
      setEntries(updatedEntries);
      setEntry(null);
      setContent('');
      setMood('neutral');
      setTags([]);
    }
  };

  const exportJournal = () => {
    const allEntries = entries
      .sort((a, b) => b.date.localeCompare(a.date))
      .map(e => '## ' + e.date + ' — ' + e.mood + '\n' + e.content + '\n\nTags: ' + e.tags.join(', '))
      .join('\n\n---\n\n');
    
    const md = '# JEBAT Journal Export\nGenerated: ' + new Date().toISOString().split('T')[0] + '\n\n' + allEntries;
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'journal-' + new Date().toISOString().split('T')[0] + '.md';
    a.click(); URL.revokeObjectURL(url);
  };

  return React.createElement('div', { className: 'space-y-6' }, [
    React.createElement('div', { className: 'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4', key: 'header' }, [
      React.createElement('div', { key: 'title' }, [
        React.createElement('h1', { className: 'text-3xl font-bold', key: 'h1' }, 'Daily Journal'),
        React.createElement('p', { className: 'text-muted-foreground', key: 'desc' }, 'Reflect, track mood, and build your personal memory'),
      ]),
      React.createElement('div', { className: 'flex items-center gap-2', key: 'actions' }, [
        React.createElement('button', { onClick: exportJournal, className: 'px-3 py-2 border rounded-lg', key: 'export' }, 'Export'),
        React.createElement('button', { onClick: () => {}, className: 'px-3 py-2 border rounded-lg', key: 'today' }, 'Today'),
      ]),
    ]),
    React.createElement('div', { className: 'flex bg-muted p-1 rounded-lg', role: 'tablist', key: 'tabs' }, [
      React.createElement('button', { role: 'tab', 'aria-selected': true, className: 'flex-1 px-3 py-2 rounded', key: 'write' }, 'Write'),
      React.createElement('button', { role: 'tab', 'aria-selected': false, className: 'flex-1 px-3 py-2 rounded', key: 'calendar' }, 'Calendar'),
    ]),
    React.createElement('div', { className: 'text-center py-8', key: 'placeholder' }, 'Journal Page - Under Construction'),
  ]);
}

export function StatCard({ label, value }: { label: string; value: string | number }) {
  return React.createElement('div', { className: 'p-3 bg-muted/50 rounded-lg' }, [
    React.createElement('p', { className: 'text-2xl font-bold', key: 'val' }, value),
    React.createElement('p', { className: 'text-xs text-muted-foreground', key: 'lbl' }, label),
  ]);
}