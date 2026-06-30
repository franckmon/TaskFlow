import { AuthGate } from './components/AuthGate';
import { AuthenticatedLayout } from './components/AuthenticatedLayout';
import { TasksPage } from './components/TasksPage';

function App() {
  return (
    <AuthGate>
      <AuthenticatedLayout>
        <TasksPage />
      </AuthenticatedLayout>
    </AuthGate>
  );
}

export default App;
