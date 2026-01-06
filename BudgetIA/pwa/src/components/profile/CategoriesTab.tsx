import React, { useState } from "react";
import { Plus, Trash2, Tag, Edit2 } from "lucide-react";
import { toast } from "sonner";

import { useCategories, useCreateCategory, useDeleteCategory, useUpdateCategory, type CreateCategoryPayload, type Category } from "../../services/categoryService";
import { GlassCard } from "../ui/GlassCard";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Skeleton } from "../ui/Skeleton";
import { GradientBanner } from "../ui/GradientBanner";
import { FormDrawer } from "../ui/FormDrawer";

// COLORS Palette
const COLORS = [
  "#2563eb", "#dc2626", "#16a34a", "#d97706", "#9333ea", 
  "#db2777", "#0891b2", "#ea580c", "#4f46e5", "#059669"
];

const getColorForCategory = (index: number) => COLORS[index % COLORS.length];

export const CategoriesTab: React.FC = () => {
    const { data: categories, isLoading, isError } = useCategories();
    const createMutation = useCreateCategory();
    const updateMutation = useUpdateCategory();
    const deleteMutation = useDeleteCategory();

    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [editingCategory, setEditingCategory] = useState<Category | null>(null);

    const [formData, setFormData] = useState({
        name: "",
        type: "Despesa",
        tags: ""
    });

    // Reset Form
    const handleCloseDrawer = () => {
        setIsDrawerOpen(false);
        setEditingCategory(null);
        setFormData({ name: "", type: "Despesa", tags: "" });
    };

    // Open for Create
    const handleOpenCreate = () => {
        setEditingCategory(null);
        setFormData({ name: "", type: "Despesa", tags: "" });
        setIsDrawerOpen(true);
    };

    // Open for Edit
    const handleOpenEdit = (cat: Category) => {
        setEditingCategory(cat);
        setFormData({
            name: cat.name,
            type: cat.type,
            tags: cat.tags || ""
        });
        setIsDrawerOpen(true);
    };

    // Submit Handler (Create or Update)
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!formData.name.trim()) {
            toast.error("O nome da categoria é obrigatório.");
            return;
        }

        const payload: CreateCategoryPayload = {
            name: formData.name.trim(),
            type: formData.type,
            tags: formData.tags.trim(),
            icon: "circle",
        };

        try {
            if (editingCategory) {
                // UPDATE
                await updateMutation.mutateAsync({ 
                    oldName: editingCategory.name, 
                    payload 
                });
                toast.success(`Categoria '${formData.name}' atualizada!`);
            } else {
                // CREATE
                await createMutation.mutateAsync(payload);
                toast.success(`Categoria '${formData.name}' criada!`);
            }
            handleCloseDrawer();
        } catch (error) {
            // Error handling done in service/query
        }
    };

    const handleDelete = async (name: string) => {
        if (!confirm(`Tem certeza que deseja apagar a categoria '${name}'?`)) return;
        try {
            await deleteMutation.mutateAsync(name);
            toast.success(`Categoria '${name}' removida.`);
        } catch (error) { }
    };

    // Filter out internal tags for display
    const formatTags = (tags?: string) => {
        if (!tags) return null;
        return tags.split(',')
            .map(t => t.trim())
            .filter(t => t !== "migrado_auto" && t.length > 0)
            .join(", ");
    };

    if (isLoading) {
        return (
            <div className="space-y-4 animate-in fade-in">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                     {[1, 2, 3].map((i) => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
                </div>
            </div>
        );
    }

    if (isError) {
        return <div className="p-4 text-center text-red-400">Erro ao carregar categorias.</div>;
    }

    return (
        <div className="space-y-6">
            <GradientBanner 
                icon={Tag}
                title="Minhas Categorias"
                description="Classifique suas transações para melhor análise."
                variant="orange"
            />
            
            <div className="flex justify-end items-center">
                <Button className="gap-2" onClick={handleOpenCreate} size="sm">
                    <Plus className="w-4 h-4" /> Nova
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {categories?.map((cat, index) => (
                    <GlassCard 
                        key={cat.name} 
                        className="relative group flex flex-col justify-between p-4 border-l-4 min-h-[120px]" 
                        style={{ borderLeftColor: getColorForCategory(index) }}
                    >
                        <div className="space-y-1">
                            <div className="flex justify-between items-start">
                                <h4 className="font-semibold text-white truncate pr-6" title={cat.name}>
                                    {cat.name}
                                </h4>
                                <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button 
                                        className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/10"
                                        onClick={() => handleOpenEdit(cat)}
                                        title="Editar"
                                    >
                                        <Edit2 className="w-3.5 h-3.5" />
                                    </button>
                                    <button 
                                        className="p-1.5 rounded-md text-gray-400 hover:text-red-400 hover:bg-red-500/10"
                                        onClick={() => handleDelete(cat.name)}
                                        title="Remover"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>
                            
                            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full inline-block ${cat.type === "Receita" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                                {cat.type}
                            </span>
                        </div>

                        {formatTags(cat.tags) && (
                             <div className="flex items-start gap-2 text-xs text-gray-500 mt-3 pt-3 border-t border-white/5">
                                <Tag className="w-3 h-3 mt-0.5 shrink-0 opacity-50" />
                                <p className="truncate opacity-70">
                                    {formatTags(cat.tags)}
                                </p>
                            </div>
                        )}
                    </GlassCard>
                ))}
            </div>

            <FormDrawer
                isOpen={isDrawerOpen}
                onClose={handleCloseDrawer}
                title={editingCategory ? "Editar Categoria" : "Nova Categoria"}
                formId="form-category"
                onSubmit={handleSubmit}
                isLoading={createMutation.isPending || updateMutation.isPending}
                submitLabel={editingCategory ? "Salvar" : "Criar"}
            >
                <div className="space-y-4">
                    <div className="space-y-2">
                        <label className="text-sm font-medium ml-1">Nome</label>
                        <Input 
                            value={formData.name}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                            placeholder="Ex: Alimentação"
                        />
                    </div>
                    
                    <div className="space-y-2">
                        <label className="text-sm font-medium ml-1">Tipo</label>
                        <Select
                            value={formData.type}
                            onChange={(e: any) => setFormData({...formData, type: e.target.value})}
                            options={[
                                { label: "Despesa", value: "Despesa" },
                                { label: "Receita", value: "Receita" }
                            ]}
                        />
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium ml-1">Tags (opcional)</label>
                        <Input 
                            value={formData.tags}
                            onChange={(e) => setFormData({...formData, tags: e.target.value})}
                            placeholder="Ex: mercado, ifood"
                        />
                        <p className="text-xs text-muted-foreground ml-1">
                            Separe por vírgulas.
                        </p>
                    </div>
                </div>
            </FormDrawer>
        </div>
    );
};
