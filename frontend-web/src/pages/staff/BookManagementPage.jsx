import { useEffect, useState } from 'react'
import { getBooks, createBook, updateBook, deleteBook } from '../../api/books'
import { getCategories } from '../../api/catalog'
import { Button } from '../../components/common/Button'
import { Input, Select, Textarea } from '../../components/common/Input'
import { Modal } from '../../components/common/Modal'
import { ConfirmDialog } from '../../components/common/ConfirmDialog'
import { Spinner } from '../../components/common/Spinner'
import { EmptyState } from '../../components/common/EmptyState'
import { ErrorBanner } from '../../components/common/ErrorBanner'
import { Badge } from '../../components/common/Badge'
import { formatCurrency } from '../../utils/format'

const EMPTY_FORM = {
  title: '', author: '', isbn: '', publisher: '',
  price: '', stock: '', description: '', image_url: '', category_id: '',
}

export default function BookManagementPage() {
  const [books, setBooks] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formErrors, setFormErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [search, setSearch] = useState('')
  const [deleteTarget, setDeleteTarget] = useState(null)

  const fetchData = () => {
    setLoading(true)
    Promise.all([getBooks(), getCategories()])
      .then(([bks, cats]) => { setBooks(bks); setCategories(cats) })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchData() }, [])

  const openCreate = () => {
    setEditing(null)
    setForm(EMPTY_FORM)
    setFormErrors({})
    setSaveError('')
    setModalOpen(true)
  }

  const openEdit = (book) => {
    setEditing(book)
    setForm({
      title: book.title || '',
      author: book.author || '',
      isbn: book.isbn || '',
      publisher: book.publisher || '',
      price: book.price || '',
      stock: String(book.stock || 0),
      description: book.description || '',
      image_url: book.image_url || '',
      category_id: String(book.category_id || ''),
      category_name_snapshot: book.category_name_snapshot || '',
    })
    setFormErrors({})
    setSaveError('')
    setModalOpen(true)
  }

  const validate = () => {
    const e = {}
    if (!form.title.trim()) e.title = 'Title is required'
    if (!form.author.trim()) e.author = 'Author is required'
    if (!form.price || isNaN(parseFloat(form.price))) e.price = 'Valid price required'
    if (!form.stock || isNaN(parseInt(form.stock))) e.stock = 'Valid stock required'
    return e
  }

  const handleSave = async () => {
    const errs = validate()
    if (Object.keys(errs).length) { setFormErrors(errs); return }
    setSaving(true)
    setSaveError('')
    try {
      const selectedCategory = categories.find((c) => String(c.id) === String(form.category_id))
      const payload = {
        ...form,
        price: parseFloat(form.price),
        stock: parseInt(form.stock),
        category_id: form.category_id ? parseInt(form.category_id) : null,
        category_name_snapshot: selectedCategory ? selectedCategory.name : '',
      }
      if (editing) {
        const updated = await updateBook(editing.id, payload)
        setBooks((bs) => bs.map((b) => (b.id === updated.id ? updated : b)))
      } else {
        const created = await createBook(payload)
        setBooks((bs) => [created, ...bs])
      }
      setModalOpen(false)
    } catch (err) {
      setSaveError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = (book) => {
    setDeleteTarget(book)
  }

  const handleDeleteConfirmed = async () => {
    if (!deleteTarget) return
    try {
      await deleteBook(deleteTarget.id)
      setBooks((bs) => bs.filter((b) => b.id !== deleteTarget.id))
    } catch (err) {
      setError(err.message)
    } finally {
      setDeleteTarget(null)
    }
  }

  const f = (name) => ({
    value: form[name],
    onChange: (e) => { setForm((prev) => ({ ...prev, [name]: e.target.value })); setFormErrors((er) => ({ ...er, [name]: '' })) },
    error: formErrors[name],
  })

  const displayed = books.filter((b) =>
    !search || b.title?.toLowerCase().includes(search.toLowerCase()) || b.author?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Book Management</h1>
          <p className="text-gray-500 text-sm">{books.length} books total</p>
        </div>
        <Button onClick={openCreate}>+ Add Book</Button>
      </div>

      <div className="flex gap-3 items-center">
        <input
          type="search"
          placeholder="Search by title or author..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />
      </div>

      <ErrorBanner message={error} />

      {loading ? (
        <Spinner />
      ) : displayed.length === 0 ? (
        <EmptyState icon="📚" title="No books yet" message="Add your first book to get started." />
      ) : (
        <div className="bg-white rounded-2xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Book</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Author</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Category</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Price</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Stock</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {displayed.map((book) => (
                <tr key={book.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-800 max-w-xs truncate">{book.title}</div>
                    {book.isbn && <div className="text-xs text-gray-400">{book.isbn}</div>}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{book.author}</td>
                  <td className="px-4 py-3">
                    {book.category_name_snapshot && (
                      <Badge color="indigo">{book.category_name_snapshot}</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-gray-800">
                    {formatCurrency(book.price)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={book.stock > 0 ? 'text-green-600 font-medium' : 'text-red-500'}>
                      {book.stock}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => openEdit(book)}
                        className="text-xs text-indigo-600 hover:underline font-medium"
                      >Edit</button>
                      <button
                        onClick={() => handleDelete(book)}
                        className="text-xs text-red-500 hover:underline font-medium"
                      >Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? 'Edit Book' : 'Add New Book'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} loading={saving}>{editing ? 'Save Changes' : 'Create Book'}</Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <ErrorBanner message={saveError} />
          <Input label="Title" required placeholder="Book title" {...f('title')} />
          <Input label="Author" required placeholder="Author name" {...f('author')} />
          <Input label="ISBN" placeholder="978-..." {...f('isbn')} />
          <Input label="Publisher" placeholder="Publisher name" {...f('publisher')} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Price (VND)" type="number" required placeholder="0" {...f('price')} />
            <Input label="Stock" type="number" required placeholder="0" {...f('stock')} />
          </div>
          <Select label="Category" {...f('category_id')}>
            <option value="">No category</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </Select>
          <Input label="Image URL" placeholder="https://..." {...f('image_url')} />
          <Textarea label="Description" placeholder="Book description..." {...f('description')} />
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirmed}
        title="Delete Book?"
        message={`Are you sure you want to delete "${deleteTarget?.title}"? This cannot be undone.`}
        confirmLabel="Delete"
        danger
      />
    </div>
  )
}
