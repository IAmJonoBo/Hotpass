/**
 * Human-in-the-Loop Store
 *
 * Manages HIL approval state and audit history using React Query for persistence.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { HILApproval, HILAuditEntry } from '@/types'

// Mock storage using localStorage
const HIL_STORAGE_KEY = 'hotpass_hil_approvals'
const HIL_AUDIT_KEY = 'hotpass_hil_audit'

function getStoredApprovals(): Record<string, HILApproval> {
  if (typeof window === 'undefined') return {}
  const stored = localStorage.getItem(HIL_STORAGE_KEY)
  return stored ? JSON.parse(stored) : {}
}

function setStoredApprovals(approvals: Record<string, HILApproval>) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(HIL_STORAGE_KEY, JSON.stringify(approvals))
  }
}

function getStoredAudit(): HILAuditEntry[] {
  if (typeof window === 'undefined') return []
  const stored = localStorage.getItem(HIL_AUDIT_KEY)
  return stored ? JSON.parse(stored) : []
}

function setStoredAudit(audit: HILAuditEntry[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(HIL_AUDIT_KEY, JSON.stringify(audit))
  }
}

export function useHILApprovals() {
  return useQuery({
    queryKey: ['hil-approvals'],
    queryFn: () => getStoredApprovals(),
  })
}

export function useHILAudit() {
  return useQuery({
    queryKey: ['hil-audit'],
    queryFn: () => getStoredAudit(),
  })
}

export function useApproveRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      runId,
      operator,
      comment,
    }: {
      runId: string
      operator: string
      comment?: string
    }) => {
      const approvals = getStoredApprovals()
      const audit = getStoredAudit()

      const approval: HILApproval = {
        id: `approval-${Date.now()}`,
        runId,
        status: 'approved',
        operator,
        timestamp: new Date().toISOString(),
        comment,
      }

      const auditEntry: HILAuditEntry = {
        id: `audit-${Date.now()}`,
        runId,
        action: 'approve',
        operator,
        timestamp: new Date().toISOString(),
        comment,
        previousStatus: approvals[runId]?.status,
        newStatus: 'approved',
      }

      approvals[runId] = approval
      setStoredApprovals(approvals)
      setStoredAudit([auditEntry, ...audit])

      return approval
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hil-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['hil-audit'] })
    },
  })
}

export function useRejectRun() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      runId,
      operator,
      reason,
      comment,
    }: {
      runId: string
      operator: string
      reason?: string
      comment?: string
    }) => {
      const approvals = getStoredApprovals()
      const audit = getStoredAudit()

      const approval: HILApproval = {
        id: `approval-${Date.now()}`,
        runId,
        status: 'rejected',
        operator,
        timestamp: new Date().toISOString(),
        reason,
        comment,
      }

      const auditEntry: HILAuditEntry = {
        id: `audit-${Date.now()}`,
        runId,
        action: 'reject',
        operator,
        timestamp: new Date().toISOString(),
        comment: reason || comment,
        previousStatus: approvals[runId]?.status,
        newStatus: 'rejected',
      }

      approvals[runId] = approval
      setStoredApprovals(approvals)
      setStoredAudit([auditEntry, ...audit])

      return approval
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hil-approvals'] })
      queryClient.invalidateQueries({ queryKey: ['hil-audit'] })
    },
  })
}

export function useGetRunApproval(runId: string) {
  return useQuery({
    queryKey: ['hil-approval', runId],
    queryFn: () => {
      const approvals = getStoredApprovals()
      return approvals[runId] || null
    },
  })
}

export function useGetRunHistory(runId: string) {
  return useQuery({
    queryKey: ['hil-history', runId],
    queryFn: () => {
      const audit = getStoredAudit()
      return audit.filter(entry => entry.runId === runId)
    },
  })
}
