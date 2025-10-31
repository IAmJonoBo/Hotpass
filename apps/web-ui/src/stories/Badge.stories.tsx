import type { Meta, StoryObj } from '@storybook/react'
import { Badge } from '@/components/ui/badge'

const meta = {
  title: 'UI/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'outline'],
    },
  },
} satisfies Meta<typeof Badge>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    children: 'Badge',
    variant: 'default',
  },
}

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
}

export const Destructive: Story = {
  args: {
    children: 'Destructive',
    variant: 'destructive',
  },
}

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
}

export const StatusBadges: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge variant="outline" className="text-green-600 dark:text-green-400">
        Completed
      </Badge>
      <Badge variant="outline" className="text-blue-600 dark:text-blue-400">
        Running
      </Badge>
      <Badge variant="outline" className="text-red-600 dark:text-red-400">
        Failed
      </Badge>
      <Badge variant="outline" className="text-yellow-600 dark:text-yellow-400">
        Pending
      </Badge>
    </div>
  ),
}

export const EnvironmentBadges: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge className="bg-blue-600 text-white">local</Badge>
      <Badge className="bg-yellow-600 text-white">staging</Badge>
      <Badge className="bg-red-600 text-white">prod</Badge>
    </div>
  ),
}
