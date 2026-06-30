import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useTasks } from '../hooks/useTasks';
import { CreateForm } from './CreateForm';
import { Search } from './Search';
import { Filters } from './Filters';
import { SortControls } from './SortControls';
import { ErrorAlert } from './ErrorAlert';
import { RefreshIndicator } from './RefreshIndicator';
import { TaskTable } from './TaskTable';
import { TaskPagination } from './TaskPagination';
import { TaskCreate } from '../types';

const INITIAL_CREATE_FORM: TaskCreate = {
  title: '',
  description: '',
  priority: 'normal',
};

// Create errors go to the form; list/mutation errors use the page-level alert.
export const TasksPage: React.FC = () => {
  const { user } = useAuth();
  const [createForm, setCreateForm] = useState<TaskCreate>(INITIAL_CREATE_FORM);
  const [showCreateError, setShowCreateError] = useState(false);

  const {
    tasks,
    isInitialLoading,
    isRefreshing,
    isCreating,
    deletingTaskId,
    updatingTaskId,
    error,
    filters,
    pagination,
    sorting,
    currentPage,
    hasNextPage,
    setStatusFilter,
    setPriorityFilter,
    setSearchFilter,
    setSortBy,
    setSortOrder,
    nextPage,
    prevPage,
    updateTaskStatus,
    removeTask,
    createTask,
  } = useTasks(true);

  const handleCreateSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setShowCreateError(false);

    const createError = await createTask(createForm);
    if (createError) {
      setShowCreateError(true);
      return;
    }

    setCreateForm(INITIAL_CREATE_FORM);
  };

  return (
    <>
      <CreateForm
        values={createForm}
        onChange={setCreateForm}
        onSubmit={handleCreateSubmit}
        isSubmitting={isCreating}
        error={showCreateError ? error : null}
      />

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <Search search={filters.search} onSearchChange={setSearchFilter} />
        <Filters
          status={filters.status}
          priority={filters.priority}
          onStatusChange={setStatusFilter}
          onPriorityChange={setPriorityFilter}
        />
        <SortControls
          sortBy={sorting.sort_by}
          sortOrder={sorting.sort_order}
          onSortByChange={setSortBy}
          onSortOrderChange={setSortOrder}
        />
      </div>

      {error && !showCreateError && <ErrorAlert message={error} />}

      {isInitialLoading ? (
        <div className="text-center py-8 text-gray-500">Loading tasks...</div>
      ) : (
        <>
          {isRefreshing && <RefreshIndicator />}

          {tasks.length === 0 ? (
            <div className="bg-white p-8 rounded-lg shadow-md text-center text-gray-500">
              No tasks found
            </div>
          ) : (
            <>
              <TaskTable
                tasks={tasks}
                onStatusChange={updateTaskStatus}
                onDelete={removeTask}
                isAdmin={user?.role === 'admin'}
                updatingTaskId={updatingTaskId}
                deletingTaskId={deletingTaskId}
              />
              <TaskPagination
                currentPage={currentPage}
                canGoPrevious={pagination.skip > 0 && !isRefreshing}
                canGoNext={hasNextPage && !isRefreshing}
                onPrevious={prevPage}
                onNext={nextPage}
              />
            </>
          )}
        </>
      )}
    </>
  );
};
