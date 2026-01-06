import { fetchAPI } from "./api";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export interface Category {
  name: string;
  type: string;
  icon: string;
  tags: string;
}

export interface CreateCategoryPayload {
  name: string;
  type: string;
  icon?: string;
  tags?: string;
}

const ENDPOINT = "/categories";

export const categoryService = {
  getAll: () => fetchAPI<Category[]>(`${ENDPOINT}/`),
  
  create: (data: CreateCategoryPayload) => 
    fetchAPI<void>(`${ENDPOINT}/`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  delete: (name: string) =>
    fetchAPI<void>(`${ENDPOINT}/${encodeURIComponent(name)}`, {
      method: "DELETE",
    }),

  update: (data: { oldName: string; payload: CreateCategoryPayload }) =>
    fetchAPI<void>(`${ENDPOINT}/${encodeURIComponent(data.oldName)}`, {
      method: "PUT",
      body: JSON.stringify(data.payload),
    }),
};

// --- React Query Hooks ---

export const useCategories = () => {
  return useQuery({
    queryKey: ["categories"],
    queryFn: categoryService.getAll,
    staleTime: 5 * 60 * 1000, 
  });
};

export const useCreateCategory = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: categoryService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });
};

export const useUpdateCategory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: categoryService.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      // Invalidate transactions as they might have been renamed cascade-style
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }); // Summary might change if we group by category
    },
  });
};

export const useDeleteCategory = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: categoryService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      // Ideally check if transactions changed, but safe to invalidate
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    },
  });
};
