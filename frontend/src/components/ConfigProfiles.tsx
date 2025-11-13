import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { profilesApi } from '@/api/client';
import { Save, Download, Trash2, Plus } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';

export default function ConfigProfiles() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [profileName, setProfileName] = useState('');
  const [profileDesc, setProfileDesc] = useState('');
  const queryClient = useQueryClient();

  const { data: profilesData } = useQuery({
    queryKey: ['profiles'],
    queryFn: () => profilesApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => profilesApi.create({ name: profileName, description: profileDesc }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      setProfileName('');
      setProfileDesc('');
      setShowCreateForm(false);
      showSuccess('Profile saved successfully');
    },
    onError: (error: any) => {
      showError(error.response?.data?.detail || 'Failed to save profile');
    },
  });

  const loadMutation = useMutation({
    mutationFn: (profileId: number) => profilesApi.load(profileId),
    onSuccess: () => {
      showSuccess('Profile loaded successfully. Refresh to see changes.');
    },
    onError: (error: any) => {
      showError(error.response?.data?.detail || 'Failed to load profile');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (profileId: number) => profilesApi.delete(profileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
      showSuccess('Profile deleted');
    },
    onError: (error: any) => {
      showError(error.response?.data?.detail || 'Failed to delete profile');
    },
  });

  const profiles = profilesData?.data?.profiles || [];

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Configuration Profiles</h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded text-sm transition-colors"
        >
          {showCreateForm ? <span>Cancel</span> : <><Plus size={16} /> Save Current</>}
        </button>
      </div>

      {showCreateForm && (
        <form onSubmit={handleCreate} className="mb-4 p-4 bg-slate-700 rounded">
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Profile Name *
              </label>
              <input
                type="text"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                placeholder="e.g., Field Operations"
                className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Description
              </label>
              <input
                type="text"
                value={profileDesc}
                onChange={(e) => setProfileDesc(e.target.value)}
                placeholder="Optional description"
                className="w-full bg-slate-600 border border-slate-500 rounded px-3 py-2 text-white"
              />
            </div>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 text-white px-4 py-2 rounded font-medium transition-colors w-full justify-center"
            >
              <Save size={18} />
              Save Profile
            </button>
          </div>
        </form>
      )}

      <div className="space-y-2">
        {profiles.length > 0 ? (
          profiles.map((profile: any) => (
            <div
              key={profile.id}
              className="flex items-center justify-between bg-slate-700 rounded p-3"
            >
              <div className="flex-1">
                <div className="text-white font-medium">{profile.name}</div>
                {profile.description && (
                  <div className="text-sm text-slate-400">{profile.description}</div>
                )}
                <div className="text-xs text-slate-500 mt-1">
                  Created: {new Date(profile.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => loadMutation.mutate(profile.id)}
                  disabled={loadMutation.isPending}
                  className="p-2 hover:bg-slate-600 rounded transition-colors text-blue-400"
                  title="Load Profile"
                >
                  <Download size={18} />
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete profile "${profile.name}"?`)) {
                      deleteMutation.mutate(profile.id);
                    }
                  }}
                  className="p-2 hover:bg-slate-600 rounded transition-colors text-red-400"
                  title="Delete Profile"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-slate-400">
            <div className="text-4xl mb-2">💾</div>
            <div>No saved profiles</div>
            <div className="text-sm mt-1">Save your current configuration to get started</div>
          </div>
        )}
      </div>
    </div>
  );
}
