import type { Meta, StoryObj } from '@storybook/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TelemetryStrip } from '../components/telemetry/TelemetryStrip'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

const meta = {
  title: 'Telemetry/TelemetryStrip',
  component: TelemetryStrip,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <div style={{ width: '100%' }}>
          <Story />
        </div>
      </QueryClientProvider>
    ),
  ],
  tags: ['autodocs'],
} satisfies Meta<typeof TelemetryStrip>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {},
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
          <div style={{ width: '100%' }}>
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
          <div style={{ width: '100%' }}>
            <Story />
          </div>
        </QueryClientProvider>
      )
    },
  ],
}
