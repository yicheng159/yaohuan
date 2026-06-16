import { apiFetch } from './api';

const dictionaryCache = {};

export async function getDictionary(category) {
  if (dictionaryCache[category]) {
    return dictionaryCache[category];
  }

  try {
    const response = await apiFetch(`/api/data-dictionaries/by_category/?category=${category}`);
    if (response.ok) {
      const data = await response.json();
      const items = data.data || [];
      dictionaryCache[category] = items;
      return items;
    }
  } catch (error) {
    console.error(`获取数据字典 ${category} 失败:`, error);
  }
  return [];
}

export async function getDictionaryOptions(category, includeAll = false) {
  const items = await getDictionary(category);
  const options = items.map(item => ({
    value: item.code,
    label: item.name
  }));
  
  if (includeAll) {
    options.unshift({ value: '全部', label: '全部' });
  }
  
  return options;
}

export async function getDictionaryNames(category, includeAll = false) {
  const items = await getDictionary(category);
  const names = items.map(item => item.name);
  
  if (includeAll) {
    names.unshift('全部');
  }
  
  return names;
}

export async function getDictionaryCodeByName(category, name) {
  const items = await getDictionary(category);
  const item = items.find(i => i.name === name);
  return item ? item.code : name;
}

export async function getDictionaryNameByCode(category, code) {
  const items = await getDictionary(category);
  const item = items.find(i => i.code === code);
  return item ? item.name : code;
}

export function clearDictionaryCache(category) {
  if (category) {
    delete dictionaryCache[category];
  } else {
    Object.keys(dictionaryCache).forEach(key => delete dictionaryCache[key]);
  }
}