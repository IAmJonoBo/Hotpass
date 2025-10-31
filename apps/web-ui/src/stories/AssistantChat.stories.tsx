import type { Meta, StoryObj } from '@storybook/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AssistantChat } from '../components/assistant/AssistantChat'

const queryClient = new QueryClient()

const meta = {
  title: 'Assistant/AssistantChat',
  component: AssistantChat,
  parameters: {
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <div style={{ width: '600px', height: '700px' }}>
          <Story />
        </div>
      </QueryClientProvider>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof AssistantChat>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {},
}

export const WithInitialMessage: Story = {
  args: {
    initialMessage: 'List all flows',
  },
}

export const DarkMode: Story = {
  args: {},
  parameters: {
    backgrounds: { default: 'dark' },
  },
  decorators: [
    (Story) => {
      document.documentElement.classList.add('dark')
      return (
        <QueryClientProvider client={queryClient}>
          <div style={{ width: '600px', height: '700px' }}>
            <Story />
          </div>
        </QueryClientProvider>
      )
    },
  ],
}

export const LightMode: Story = {
  args: {},
  parameters: {
    backgrounds: { default: 'light' },
  },
  decorators: [
    (Story) => {
      document.documentElement.classList.remove('dark')
      return (
        <QueryClientProvider client={queryClient}>
          <div style={{ width: '600px', height: '700px' }}>
            <Story />
          </div>
        </QueryClientProvider>
      )
    },
  ],
}
